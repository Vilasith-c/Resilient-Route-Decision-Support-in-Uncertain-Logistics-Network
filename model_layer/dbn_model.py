"""
dbn_model.py — Pipeline Stages 4 & 5: BN Structure + DBN Temporal Layer

Builds a "two-time-slice DBN" as a plain pgmpy BayesianNetwork with
explicitly duplicated nodes (Hub4_Weather_t0, Hub4_Weather_t1, etc.)
instead of using pgmpy's DynamicBayesianNetwork class.

WHY NOT DynamicBayesianNetwork:
    pgmpy's DBNInference class has a track record of fragility — errors on
    self-loops, "CPD doesn't have proper parents" errors, and open bugs.
    The duplicated-node approach gives us the SAME two-time-slice Jiang et
    al. temporal mechanic while using the stable, well-tested
    VariableElimination inference path.

Node naming convention:
    "{HubName}_{VarType}_t{slice}"
    e.g. "Hub4_Weather_t0", "Hub4_Delay_t0", "Hub4_Weather_t1", "Hub4_Delay_t1"

CPT sources:
    - Delay nodes: seeded from skew-t discretization (delay_distribution.py)
    - Weather/congestion cause nodes: expert-elicited (Wageningen methodology,
      PRD 1 §3.4)
    - Temporal transition CPTs: encode decay/persistence (a disruption at t0
      has diminished but non-zero effect at t1)

Critical rule (PRD 1 §3.6):
    Do NOT train CPTs with raw Baum-Welch/EM — the RDBN airline paper's own
    authors flag this as "inherently sub-optimal."
"""

from __future__ import annotations
from typing import Any

import networkx as nx
import numpy as np
try:
    from pgmpy.models import DiscreteBayesianNetwork as BayesianNetwork
except ImportError:
    from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD

from . import delay_distribution


# ---------------------------------------------------------------------------
# BN variable types and their states
# ---------------------------------------------------------------------------
WEATHER_STATES = ["Clear", "LightRain", "HeavyRain"]
CONGESTION_STATES = ["Low", "Medium", "High"]
DELAY_STATES = ["Low", "Medium", "High"]

# Hubs that have weather variables
WEATHER_HUBS = [
    "Hub1", "Hub2", "Hub3",     # row 0 (northern exposure)
    "Hub4", "Hub5", "Hub6",     # row 1
    "Hub10", "Hub11", "Hub12",  # row 3 (southern exposure)
]

# Hubs that have congestion variables
CONGESTION_HUBS = [
    "Hub5", "Hub8", "Hub14",    # mid-column bottlenecks
    "Hub4", "Hub11",            # high-risk hubs
]

# All hubs have delay variables
ALL_HUBS = [f"Hub{i}" for i in range(1, 19)]


def _weather_prior() -> list[float]:
    """Expert-elicited prior for weather: mostly clear."""
    return [0.60, 0.25, 0.15]  # Clear, LightRain, HeavyRain


def _congestion_prior() -> list[float]:
    """Expert-elicited prior for congestion."""
    return [0.50, 0.35, 0.15]  # Low, Medium, High


def _delay_cpd_given_weather(
    cpt_seed: dict[str, float] | None = None,
) -> np.ndarray:
    """
    CPT: P(Delay | Weather) — 3×3 matrix.

    Rows = delay states (Low, Med, High), Cols = weather states.

    When no weather disruption, delays are mostly Low.
    Under HeavyRain, delays shift heavily toward High.
    """
    if cpt_seed:
        # Use skew-t discretized values as the baseline, then shift
        # conditional on weather state
        p_l, p_m, p_h = cpt_seed["Low"], cpt_seed["Medium"], cpt_seed["High"]
        return np.array([
            # Clear          LightRain       HeavyRain
            [0.70,           0.35,           p_l * 0.5],      # Low
            [0.25,           0.40,           p_m],             # Medium
            [0.05,           0.25,           p_h + p_l * 0.5], # High
        ])
    else:
        return np.array([
            [0.70, 0.35, 0.10],  # Low
            [0.25, 0.40, 0.30],  # Medium
            [0.05, 0.25, 0.60],  # High
        ])


def _delay_cpd_given_congestion(
    cpt_seed: dict[str, float] | None = None,
) -> np.ndarray:
    """
    CPT: P(Delay | Congestion) — 3×3 matrix.
    """
    if cpt_seed:
        p_l, p_m, p_h = cpt_seed["Low"], cpt_seed["Medium"], cpt_seed["High"]
        return np.array([
            [0.65,           0.30,           p_l * 0.4],
            [0.30,           0.45,           p_m],
            [0.05,           0.25,           p_h + p_l * 0.6],
        ])
    else:
        return np.array([
            [0.65, 0.30, 0.10],
            [0.30, 0.45, 0.35],
            [0.05, 0.25, 0.55],
        ])


def _delay_cpd_given_weather_and_congestion(
    cpt_seed: dict[str, float] | None = None,
) -> np.ndarray:
    """
    CPT: P(Delay | Weather, Congestion) — 3×9 matrix.

    Parent combinations: 3 weather × 3 congestion = 9 columns.
    Column order (pgmpy convention): iterates over parents in order added.
    Weather varies slowest, Congestion varies fastest.
    """
    # Build a 3 × 3 × 3 tensor, then reshape to 3 × 9
    # [delay_state, weather_state, congestion_state]
    cpd = np.zeros((3, 3, 3))

    for w in range(3):  # weather: Clear, LightRain, HeavyRain
        for c in range(3):  # congestion: Low, Medium, High
            severity = (w + c) / 4.0  # 0..1 combined severity
            # Higher severity shifts probability toward High delay
            cpd[0, w, c] = max(0.05, 0.70 - severity * 0.60)  # Low
            cpd[2, w, c] = max(0.05, 0.05 + severity * 0.60)  # High
            cpd[1, w, c] = 1.0 - cpd[0, w, c] - cpd[2, w, c]  # Medium

    # Reshape: rows=delay_states, cols=parent_combos (weather×congestion)
    return cpd.reshape(3, 9)


def _temporal_transition_cpd() -> np.ndarray:
    """
    CPT: P(X_t1 | X_t0) — temporal persistence/decay.

    Encodes that a state at t0 has a high probability of persisting into t1,
    but can also recover (e.g., HeavyRain at t0 has 60% chance of persisting,
    30% of improving to LightRain, 10% of clearing).
    """
    return np.array([
        # X_t0=State0   State1    State2
        [0.70,          0.20,     0.10],   # X_t1=State0
        [0.20,          0.60,     0.30],   # X_t1=State1
        [0.10,          0.20,     0.60],   # X_t1=State2
    ])


def _delay_only_prior(
    cpt_seed: dict[str, float] | None = None,
) -> list[float]:
    """Prior for delay nodes in hubs that have no weather/congestion parent."""
    if cpt_seed:
        return [cpt_seed["Low"], cpt_seed["Medium"], cpt_seed["High"]]
    return [0.60, 0.30, 0.10]


def _normalize_columns(arr: np.ndarray) -> np.ndarray:
    """Ensure each column of a CPT sums to 1.0."""
    col_sums = arr.sum(axis=0, keepdims=True)
    col_sums = np.where(col_sums == 0, 1.0, col_sums)
    return arr / col_sums


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_bn(
    G: nx.DiGraph,
    corridors: dict[str, list[tuple[str, str]]],
    cpt_seeds: dict[str, dict[str, float]] | None = None,
    include_temporal: bool = False,
) -> BayesianNetwork:
    """
    Build a Bayesian Network for the logistics graph.

    Parameters
    ----------
    G : nx.DiGraph
        Logistics graph from graph_builder.
    corridors : dict
        Corridor definitions from corridor_model.
    cpt_seeds : dict or None
        {corridor_id: {"Low": p, "Medium": p, "High": p}} from
        delay_distribution.discretize_to_cpt_states().
        If None, uses expert-elicited defaults.
    include_temporal : bool
        If True, builds a two-time-slice model with _t0 and _t1 nodes.
        If False, builds a single-slice static BN (faster for initial demo).

    Returns
    -------
    BayesianNetwork
        A pgmpy BayesianNetwork ready for VariableElimination inference.
    """
    edges = []
    cpds = []

    slices = [0, 1] if include_temporal else [0]

    for t in slices:
        suffix = f"_t{t}"

        # --- Weather nodes (root causes) ---
        for hub in WEATHER_HUBS:
            w_node = f"{hub}_Weather{suffix}"

            if t == 0:
                # t0: unconditional prior
                cpd = TabularCPD(
                    variable=w_node,
                    variable_card=3,
                    values=[[p] for p in _weather_prior()],
                    state_names={w_node: WEATHER_STATES},
                )
                cpds.append(cpd)
            else:
                # t1: conditioned on t0 (temporal transition)
                w_prev = f"{hub}_Weather_t0"
                edges.append((w_prev, w_node))
                trans = _normalize_columns(_temporal_transition_cpd())
                cpd = TabularCPD(
                    variable=w_node,
                    variable_card=3,
                    values=trans.tolist(),
                    evidence=[w_prev],
                    evidence_card=[3],
                    state_names={
                        w_node: WEATHER_STATES,
                        w_prev: WEATHER_STATES,
                    },
                )
                cpds.append(cpd)

        # --- Congestion nodes (root causes) ---
        for hub in CONGESTION_HUBS:
            c_node = f"{hub}_Congestion{suffix}"

            if t == 0:
                cpd = TabularCPD(
                    variable=c_node,
                    variable_card=3,
                    values=[[p] for p in _congestion_prior()],
                    state_names={c_node: CONGESTION_STATES},
                )
                cpds.append(cpd)
            else:
                c_prev = f"{hub}_Congestion_t0"
                edges.append((c_prev, c_node))
                trans = _normalize_columns(_temporal_transition_cpd())
                cpd = TabularCPD(
                    variable=c_node,
                    variable_card=3,
                    values=trans.tolist(),
                    evidence=[c_prev],
                    evidence_card=[3],
                    state_names={
                        c_node: CONGESTION_STATES,
                        c_prev: CONGESTION_STATES,
                    },
                )
                cpds.append(cpd)

        # --- Delay nodes (effects) ---
        for hub in ALL_HUBS:
            d_node = f"{hub}_Delay{suffix}"

            has_weather = hub in WEATHER_HUBS
            has_congestion = hub in CONGESTION_HUBS

            # Look up CPT seed for this hub's corridor
            hub_cpt_seed = None
            if cpt_seeds:
                for cid, cedges in corridors.items():
                    for (s, d) in cedges:
                        if s == hub or d == hub:
                            if cid in cpt_seeds:
                                hub_cpt_seed = cpt_seeds[cid]
                                break
                    if hub_cpt_seed:
                        break

            if has_weather and has_congestion:
                w_node = f"{hub}_Weather{suffix}"
                c_node = f"{hub}_Congestion{suffix}"
                edges.append((w_node, d_node))
                edges.append((c_node, d_node))

                values = _normalize_columns(
                    _delay_cpd_given_weather_and_congestion(hub_cpt_seed)
                )
                parents = [w_node, c_node]
                parent_cards = [3, 3]
                state_names = {
                    d_node: DELAY_STATES,
                    w_node: WEATHER_STATES,
                    c_node: CONGESTION_STATES,
                }

            elif has_weather:
                w_node = f"{hub}_Weather{suffix}"
                edges.append((w_node, d_node))

                values = _normalize_columns(
                    _delay_cpd_given_weather(hub_cpt_seed)
                )
                parents = [w_node]
                parent_cards = [3]
                state_names = {
                    d_node: DELAY_STATES,
                    w_node: WEATHER_STATES,
                }

            elif has_congestion:
                c_node = f"{hub}_Congestion{suffix}"
                edges.append((c_node, d_node))

                values = _normalize_columns(
                    _delay_cpd_given_congestion(hub_cpt_seed)
                )
                parents = [c_node]
                parent_cards = [3]
                state_names = {
                    d_node: DELAY_STATES,
                    c_node: CONGESTION_STATES,
                }

            else:
                # No causal parents — use unconditional prior
                prior = _delay_only_prior(hub_cpt_seed)
                cpd = TabularCPD(
                    variable=d_node,
                    variable_card=3,
                    values=[[p] for p in prior],
                    state_names={d_node: DELAY_STATES},
                )
                cpds.append(cpd)

                # Add temporal edge if t1
                if t == 1:
                    d_prev = f"{hub}_Delay_t0"
                    edges.append((d_prev, d_node))
                    # Override with temporal CPD
                    trans = _normalize_columns(_temporal_transition_cpd())
                    cpd = TabularCPD(
                        variable=d_node,
                        variable_card=3,
                        values=trans.tolist(),
                        evidence=[d_prev],
                        evidence_card=[3],
                        state_names={
                            d_node: DELAY_STATES,
                            d_prev: DELAY_STATES,
                        },
                    )
                    # Replace the just-added unconditional CPD
                    cpds[-1] = cpd
                continue

            # For nodes with causal parents, add temporal edge at t1
            if t == 1:
                d_prev = f"{hub}_Delay_t0"
                edges.append((d_prev, d_node))
                parents.append(d_prev)
                parent_cards.append(3)
                state_names[d_prev] = DELAY_STATES

                # Expand CPT to include temporal parent
                # Original shape: (3, n_parent_combos)
                # New shape: (3, n_parent_combos * 3)
                n_prev_cols = values.shape[1]
                expanded = np.zeros((3, n_prev_cols * 3))
                for prev_state in range(3):
                    # Weight: blend of causal CPT and temporal persistence
                    causal_weight = 0.6
                    temporal_weight = 0.4
                    temporal_col = _temporal_transition_cpd()[:, prev_state]

                    for col in range(n_prev_cols):
                        new_col = col * 3 + prev_state
                        blended = causal_weight * values[:, col] + temporal_weight * temporal_col
                        expanded[:, new_col] = blended

                values = _normalize_columns(expanded)

            cpd = TabularCPD(
                variable=d_node,
                variable_card=3,
                values=values.tolist(),
                evidence=parents,
                evidence_card=parent_cards,
                state_names=state_names,
            )
            cpds.append(cpd)

    # Build the BN
    bn = BayesianNetwork(edges)
    for cpd in cpds:
        bn.add_cpds(cpd)

    # Validate
    assert bn.check_model(), "BN model validation failed — check CPD shapes and parent ordering"

    return bn


def get_evidence_variables(bn: BayesianNetwork, time_slice: int = 0) -> dict[str, list[str]]:
    """
    Return the evidence variables available for a given time slice,
    grouped by type.

    Returns
    -------
    dict[str, list[str]]
        {"weather": [...], "congestion": [...]}
    """
    suffix = f"_t{time_slice}"
    weather = [n for n in bn.nodes() if "_Weather" in n and n.endswith(suffix)]
    congestion = [n for n in bn.nodes() if "_Congestion" in n and n.endswith(suffix)]
    return {"weather": sorted(weather), "congestion": sorted(congestion)}


def get_delay_nodes(bn: BayesianNetwork, time_slice: int = 0) -> list[str]:
    """Return all delay node names for a given time slice."""
    suffix = f"_t{time_slice}"
    return sorted([n for n in bn.nodes() if "_Delay" in n and n.endswith(suffix)])


def get_all_node_names(bn: BayesianNetwork) -> list[str]:
    """Return sorted list of all node names in the BN."""
    return sorted(bn.nodes())
