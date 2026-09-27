"""
engine.py — Orchestration entry point for the Inference Engine (PRD 6 §5)

Orchestrates calls between model_layer and inference_runner to produce
the single ENGINE_RESULT dictionary consumed by the frontend (PRD 7).
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

import networkx as nx
from pgmpy.models import BayesianNetwork

from model_layer import (
    graph_builder,
    corridor_model,
    delay_distribution,
    dbn_model,
    reliability_ranking,
    resilience_metrics,
)
from .engine_state import EngineState
from .inference_runner import run_inference, validate_evidence


def initialize_engine(
    include_temporal: bool = True,
    time_budget: float = 200.0,
) -> tuple[nx.DiGraph, BayesianNetwork, EngineState, dict[str, Any]]:
    """
    Initialize the complete system from scratch.

    1. Builds the 20-node directed logistics graph.
    2. Identifies and assigns edge corridors.
    3. Fits/seeds skew-t delay distributions per corridor.
    4. Builds the two-time-slice Bayesian Network.
    5. Computes the baseline (unconditional) ENGINE_RESULT.

    Parameters
    ----------
    include_temporal : bool
        Whether to build the two-time-slice DBN (True) or static BN (False).
    time_budget : float
        Maximum cumulative travel time budget for route ranking.

    Returns
    -------
    tuple[nx.DiGraph, BayesianNetwork, EngineState, dict]
        (G, bn, state, baseline_result)
    """
    # 1. Graph
    G = graph_builder.build_logistics_graph()

    # 2. Corridors
    corridors = corridor_model.define_corridors(G)
    corridor_model.assign_corridor_ids(G, corridors)

    # 3. Delay distribution CPT seeds
    cpt_seeds = {}
    for cid in corridor_model.get_all_corridor_ids(G):
        samples = delay_distribution.generate_synthetic_delay_samples(
            n_samples=100,
            base_travel_time=20.0,
            disruption_prob=0.15 if "weather" in cid or "congestion" in cid else 0.05,
        )
        fit = delay_distribution.fit_corridor_distribution(samples)
        cpt_seeds[cid] = delay_distribution.discretize_to_cpt_states(fit)

    # 4. Bayesian Network
    bn = dbn_model.build_bn(
        G=G,
        corridors=corridors,
        cpt_seeds=cpt_seeds,
        include_temporal=include_temporal,
    )

    # 5. State and baseline result
    state = EngineState()
    initial_result = update_evidence(
        state=state,
        bn=bn,
        G=G,
        new_evidence={},
        time_budget=time_budget,
    )

    return G, bn, state, initial_result


def update_evidence(
    state: EngineState,
    bn: BayesianNetwork,
    G: nx.DiGraph,
    new_evidence: dict[str, str],
    time_budget: float = 200.0,
    source: str = "Warehouse",
    target: str = "DeliveryZone",
    max_candidates: int = 40,
) -> dict[str, Any]:
    """
    Full pipeline Stage 4-8 orchestration for one evidence update.
    Returns an ENGINE_RESULT dict per the PRD 4 §5 data contract.

    Parameters
    ----------
    state : EngineState
        Active session state tracking evidence and history.
    bn : BayesianNetwork
        The Bayesian Network model.
    G : nx.DiGraph
        The logistics graph.
    new_evidence : dict
        Evidence to apply, e.g. {"Hub4_Weather_t0": "HeavyRain"}.
    time_budget : float
        Cumulative travel time ceiling for RSPP search.
    source : str
        Origin node.
    target : str
        Destination node.
    max_candidates : int
        Maximum candidates to generate during RSPP search.

    Returns
    -------
    dict
        ENGINE_RESULT dictionary.
    """
    # Normalize evidence keys if user/UI omitted time suffix
    normalized_evidence = {}
    valid_nodes = set(bn.nodes())
    t_suffix = f"_t{state.current_time_slice}"

    for k, v in new_evidence.items():
        if k in valid_nodes:
            normalized_evidence[k] = v
        elif f"{k}{t_suffix}" in valid_nodes:
            normalized_evidence[f"{k}{t_suffix}"] = v
        elif f"{k}_t0" in valid_nodes:
            normalized_evidence[f"{k}_t0"] = v
        else:
            normalized_evidence[k] = v  # will be caught by validate_evidence

    # Validate evidence
    if normalized_evidence:
        validate_evidence(bn, normalized_evidence)
        state.apply_evidence(normalized_evidence)

    # Run inference for current time slice
    # Note: query time slice is capped at 1 for a two-time-slice model
    query_slice = min(state.current_time_slice, 1) if any("_t1" in n for n in bn.nodes()) else 0
    posteriors = run_inference(
        bn=bn,
        evidence=state.applied_evidence,
        time_slice=query_slice,
    )

    # Route ranking via RSPP-A* with FSD pruning
    try:
        ranked_labels = reliability_ranking.rspp_astar(
            G=G,
            source=source,
            target=target,
            time_budget=time_budget,
            posteriors=posteriors,
            max_candidates=max_candidates,
        )
    except Exception:
        # Fallback to RSPP-LS if heuristic fails
        ranked_labels = reliability_ranking.rspp_ls(
            G=G,
            source=source,
            target=target,
            time_budget=time_budget,
            posteriors=posteriors,
            max_candidates=max_candidates,
        )

    # Fallback if time_budget was too tight and no route reached target
    if not ranked_labels:
        ranked_labels = reliability_ranking.rspp_ls(
            G=G,
            source=source,
            target=target,
            time_budget=time_budget * 1.5,
            posteriors=posteriors,
            max_candidates=max_candidates,
        )

    ranked_routes = [
        reliability_ranking.label_to_dict(l, max_time=time_budget * 1.2)
        for l in ranked_labels
    ]

    # Resilience metrics
    history_posteriors = state.get_posteriors_history() + [posteriors]
    scorecard = resilience_metrics.compute_resilience_scorecard(history_posteriors)
    vulnerable_hub = resilience_metrics.identify_vulnerable_hub(G, posteriors)
    risk_edge = resilience_metrics.identify_high_risk_edge(G, posteriors)
    formatted_edge = resilience_metrics.format_edge_name(risk_edge)

    recommended_id = ranked_routes[0]["route_id"] if ranked_routes else None

    # Graph structure metadata for frontend rendering (no networkx import needed in UI)
    network_graph = {
        "nodes": [
            {
                "id": n,
                "pos": G.nodes[n].get("pos", (0.0, 0.0)),
                "type": G.nodes[n].get("node_type", "hub"),
                "risk": G.nodes[n].get("risk_level", "normal"),
            }
            for n in G.nodes()
        ],
        "edges": [
            {
                "source": u,
                "target": v,
                "travel_time": d.get("base_travel_time", 20.0),
                "corridor": d.get("corridor_id"),
            }
            for u, v, d in G.edges(data=True)
        ],
    }

    engine_result: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "time_slice": state.current_time_slice,
        "evidence_applied": dict(state.applied_evidence),
        "posteriors": posteriors,
        "ranked_routes": ranked_routes,
        "resilience_scorecard": scorecard,
        "vulnerable_hub": vulnerable_hub,
        "high_risk_edge": formatted_edge,
        "recommended_route_id": recommended_id,
        "network_graph": network_graph,
    }

    state.history.append(engine_result)
    return engine_result
