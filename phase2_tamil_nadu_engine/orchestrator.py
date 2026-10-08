"""
orchestrator.py — Unified 8-Stage Timeline & Simulation Orchestrator
===================================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Module: Full 8-Stage Algorithmic Pipeline Implementation

The 8-Stage Simulation Pipeline (PRD 3, 5, 8, 9, 10):
  - Stage 1: Network Construction (43-node Tamil Nadu hierarchy with real coordinates)
  - Stage 2: Uncertainty Modeling (SPOTAR / PACE Path-Centric Corridor Dependency Model)
  - Stage 3: Delay Distribution (Metro Post-Disruption Skew-t Heavy-Tailed Discretization)
  - Stage 4: Bayesian Network Structure & Spatial Hazard Interception (Continuous exposure)
  - Stage 5: DBN Belief Propagation across t_0 ... t_H (Persistence, Contagion, & Recovery)
  - Stage 6: Reliability Ranking via RSPP-A* with FSD Dominance Pruning (Chen et al. 2012)
  - Stage 7: Resilience Scoring (Jiang et al. 2020: 5 DBN Capabilities)
  - Stage 8: Unified ENGINE_TIMELINE_RESULT Payload Assembly
"""

from __future__ import annotations
import time
import copy
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field

import numpy as np
import networkx as nx

# Local modules
from hazard_exposure import (
    HazardInput,
    HazardExposureEngine,
    NodeExposureResult,
    EdgeExposureResult,
)
from corridor_model import (
    TAMIL_NADU_CORRIDORS,
    assign_edges_to_corridors,
)
from delay_distribution import (
    get_all_corridor_discretized_priors,
    fit_and_discretize_corridor,
)
from phase1_benchmark import (
    TN_NODES,
    build_tamil_nadu_network,
    RSPPAStarSolver,
    haversine_distance_km,
)


# ---------------------------------------------------------------------------
# Output Schemas conforming strictly to PRD 1, 5, 9, 10
# ---------------------------------------------------------------------------

class RouteStatus(BaseModel):
    route_id: str
    source: str
    target: str
    corridor_id: str
    corridor_name: str
    distance_km: float
    travel_time_hr: float
    operational_pct: float
    status: str  # "Normal" | "Delayed" | "Severely Disrupted"


class CascadeEffect(BaseModel):
    node: str
    time_hour: int
    cause: str
    impact: str
    severity: float  # [0.0, 1.0]


class TimelineFrame(BaseModel):
    time_hour: int
    node_states: Dict[str, str]  # node_id -> "Low" | "Medium" | "High"
    node_posteriors: Dict[str, Dict[str, float]]  # node_id -> {"Low": p, "Medium": p, "High": p}
    corridor_disruptions: Dict[str, float]  # corridor_id -> mean disruption probability
    route_status: List[RouteStatus]
    cascade_effects: List[CascadeEffect]
    network_operational_index: float  # [0.0, 1.0]


class JiangResilienceScorecard(BaseModel):
    """
    The Five Dynamic Bayesian Network Resilience Capabilities from Jiang et al. (PRD 1 §3.5, PRD 5 §8).
    Adapted from computer-network DBNs to physical multimodal logistics networks.
    """
    rapid_response: float = Field(
        ...,
        description="Speed and magnitude of posterior state transition at disruption onset (t_0 -> t_1)"
    )
    sustained_resistance: float = Field(
        ...,
        description="Ability of network to maintain low delay probabilities under ongoing disruption (1 - max P(High))"
    )
    continuous_running: float = Field(
        ...,
        description="Temporal stability and retention of non-dominated Pareto routes across time slices"
    )
    rapid_convergence: float = Field(
        ...,
        description="Speed at which posteriors recover toward baseline after peak shock (t_peak -> t_H)"
    )
    dynamic_evolution: float = Field(
        ...,
        description="Overall trajectory trend and terminal capability of network reliability across time slices"
    )
    overall_resilience_index: float = Field(
        ...,
        description="Composite resilience index across all 5 Jiang et al. capabilities"
    )


class EngineTimelineResult(BaseModel):
    """Unified payload conforming to PRD 9 §6 and PRD 10 §3."""
    hazard_applied: HazardInput
    frames: List[TimelineFrame]
    resilience_scorecard: JiangResilienceScorecard
    vulnerable_hub: str
    high_risk_edge: str
    primary_rerouted_solutions: List[Dict[str, Any]]
    execution_time_ms: float
    network_summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# 8-Stage Simulation Orchestrator
# ---------------------------------------------------------------------------

class SimulationOrchestrator:
    """
    Unified engine managing the 8-stage simulation pipeline.
    """

    def __init__(self, base_graph: Optional[nx.DiGraph] = None):
        self.base_graph = base_graph if base_graph is not None else build_tamil_nadu_network()

        # Stage 2: Assign all edges to the 8 macro corridors (PACE/SPOTAR model)
        self.corridor_membership = assign_edges_to_corridors(self.base_graph)

        # Stage 3: Precompute skew-t discretized delay priors per corridor
        self.corridor_skew_priors = get_all_corridor_discretized_priors()

        self.node_list = list(TN_NODES.keys())
        self.node_to_idx = {n: i for i, n in enumerate(self.node_list)}
        self.num_nodes = len(self.node_list)

        # Precompute spatial adjacency matrix for network contagion
        self.adj_matrix = np.zeros((self.num_nodes, self.num_nodes), dtype=np.float64)
        for u, v in self.base_graph.edges():
            self.adj_matrix[self.node_to_idx[u], self.node_to_idx[v]] = 1.0

        row_sums = self.adj_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        self.adj_norm = self.adj_matrix / row_sums

        # Temporal Markov Transition Matrix T (3x3): [Low, Medium, High]
        self.T_mat = np.array([
            [0.86, 0.11, 0.03],  # Low
            [0.28, 0.62, 0.10],  # Medium decays toward Low
            [0.05, 0.35, 0.60],  # High recovers to Medium
        ], dtype=np.float64)

    def run_simulation(self, hazard: HazardInput) -> EngineTimelineResult:
        """
        Executes the full 8-Stage simulation pipeline for an interactive hazard event.
        """
        t_start = time.perf_counter()

        # -------------------------------------------------------------------
        # STAGE 1: Spatial Hazard Interception (Continuous exposure)
        # -------------------------------------------------------------------
        node_exposures: Dict[str, NodeExposureResult] = {}
        for nid, ndata in TN_NODES.items():
            node_exposures[nid] = HazardExposureEngine.evaluate_node_exposure(
                node_id=nid,
                node_lat=ndata["lat"],
                node_lon=ndata["lon"],
                hazard=hazard
            )

        edge_exposures: Dict[str, EdgeExposureResult] = {}
        for u, v in self.base_graph.edges():
            edge_id = f"{u}__{v}"
            edge_exposures[edge_id] = HazardExposureEngine.evaluate_edge_exposure(
                source_id=u,
                target_id=v,
                src_lat=TN_NODES[u]["lat"],
                src_lon=TN_NODES[u]["lon"],
                dst_lat=TN_NODES[v]["lat"],
                dst_lon=TN_NODES[v]["lon"],
                hazard=hazard
            )

        # -------------------------------------------------------------------
        # STAGE 2: Path-Centric Corridor Dependency Model (SPOTAR / PACE)
        # -------------------------------------------------------------------
        # Aggregate corridor-level disruption: an event hitting any link or node
        # in a corridor activates shared correlated uncertainty across all member links.
        corridor_max_exposure: Dict[str, float] = {cid: 0.0 for cid in TAMIL_NADU_CORRIDORS.keys()}

        for edge_id, edge_res in edge_exposures.items():
            u, v = edge_res.source, edge_res.target
            cid = self.base_graph[u][v].get("corridor_id", "corridor_nh44_central_artery")
            if edge_res.exposure_ratio > corridor_max_exposure[cid]:
                corridor_max_exposure[cid] = edge_res.exposure_ratio

        # Path-centric correlation coupling: member edges inherit correlated corridor shock
        degraded_graph = copy.deepcopy(self.base_graph)
        for u, v, data in degraded_graph.edges(data=True):
            edge_id = f"{u}__{v}"
            raw_exp = edge_exposures[edge_id]
            cid = data.get("corridor_id", "corridor_nh44_central_artery")

            # Correlated joint exposure: 70% direct edge intercept + 30% corridor-wide correlation
            correlated_exposure = max(
                raw_exp.exposure_ratio,
                0.70 * raw_exp.exposure_ratio + 0.30 * corridor_max_exposure[cid]
            )

            # Continuous degradation scaling
            hz_weights = HazardExposureEngine.HAZARD_SEVERITY_WEIGHTS.get(
                hazard.hazard_type.lower(),
                HazardExposureEngine.HAZARD_SEVERITY_WEIGHTS["flood"]
            )
            tt_factor = 1.0 + (hz_weights["edge_delay"] - 1.0) * correlated_exposure
            rel_mult = max(0.05, 1.0 - hz_weights["reliability_drain"] * correlated_exposure)
            op_pct = max(0.05, 1.0 - 0.90 * correlated_exposure)

            data["travel_time_hr"] = round(data["travel_time_hr"] * tt_factor, 2)
            data["on_time_prob"] = round(data["on_time_prob"] * rel_mult, 4)
            data["disruption_prob"] = round(1.0 - data["on_time_prob"], 4)
            data["operational_pct"] = round(op_pct, 4)

        # -------------------------------------------------------------------
        # STAGE 3 & 4: Skew-t CPT Seeding & Bayesian Belief Propagation (t_0)
        # -------------------------------------------------------------------
        horizon = hazard.time_horizon
        # Initialize state matrix S: [num_nodes x 3] (Low, Med, High)
        S = np.zeros((self.num_nodes, 3), dtype=np.float64)

        for i, nid in enumerate(self.node_list):
            exp = node_exposures[nid]
            # Use skew-t baseline prior as foundation
            # Find primary corridor associated with this node
            assigned_corridor = "corridor_nh44_central_artery"
            for _, _, d in self.base_graph.out_edges(nid, data=True):
                assigned_corridor = d.get("corridor_id", assigned_corridor)
                break

            prior = self.corridor_skew_priors[assigned_corridor]

            # Shift baseline conditional on continuous exposure
            e = exp.exposure_ratio
            if e > 0.0:
                p_high = min(0.95, prior["High"] + e * 0.85)
                p_med = min(0.80, prior["Medium"] + e * 0.15)
                p_low = max(0.02, 1.0 - p_high - p_med)
                total = p_low + p_med + p_high
                S[i] = [p_low / total, p_med / total, p_high / total]
            else:
                S[i] = [prior["Low"], prior["Medium"], prior["High"]]

        # -------------------------------------------------------------------
        # STAGE 5: Temporal DBN Belief Propagation across t_0 ... t_H
        # -------------------------------------------------------------------
        lambda_spatial = 0.25  # Spatial spillover along transit edges
        timeline_posteriors: List[np.ndarray] = [S.copy()]

        for step in range(1, horizon + 1):
            S_temporal = S @ self.T_mat
            S_spatial = self.adj_norm @ S_temporal
            S = (1.0 - lambda_spatial) * S_temporal + lambda_spatial * S_spatial
            S /= S.sum(axis=1, keepdims=True)
            timeline_posteriors.append(S.copy())

        # Cascade tracking
        all_cascade_effects: List[List[CascadeEffect]] = []
        for t, S_t in enumerate(timeline_posteriors):
            step_cascades = []
            for i, nid in enumerate(self.node_list):
                p_high = S_t[i, 2]
                p_med = S_t[i, 1]
                if p_high >= 0.40:
                    step_cascades.append(CascadeEffect(
                        node=nid,
                        time_hour=t,
                        cause=f"{hazard.hazard_type.capitalize()} path-centric corridor contagion",
                        impact="Severe operational disruption & bottleneck",
                        severity=round(float(p_high), 3)
                    ))
                elif p_med >= 0.45 and t > 0:
                    step_cascades.append(CascadeEffect(
                        node=nid,
                        time_hour=t,
                        cause="Secondary corridor transit delay propagation",
                        impact="Elevated congestion & delay risk",
                        severity=round(float(p_med), 3)
                    ))
            all_cascade_effects.append(step_cascades)

        # -------------------------------------------------------------------
        # STAGE 6: RSPP-A* Dynamic Re-routing across Pareto Frontiers
        # -------------------------------------------------------------------
        rspp_solver = RSPPAStarSolver(degraded_graph)
        rspp_results = rspp_solver.find_pareto_reliable_paths(
            source="HQ_Chennai",
            target="WH_30_Nagercoil",
            alpha_min_reliability=0.30
        )
        primary_solutions = rspp_results.get("pareto_solutions", [])

        # Adaptive relaxation fallback: if severe shock degrades all corridors below 0.30,
        # progressively search with lower alpha thresholds so the engine always provides
        # the best-effort resilient route rather than returning empty solutions.
        if not primary_solutions:
            for fallback_alpha in [0.15, 0.05, 0.01, 0.0001]:
                rspp_fallback = rspp_solver.find_pareto_reliable_paths(
                    source="HQ_Chennai",
                    target="WH_30_Nagercoil",
                    alpha_min_reliability=fallback_alpha
                )
                primary_solutions = rspp_fallback.get("pareto_solutions", [])
                if primary_solutions:
                    break

        # Bottleneck Identification
        hub_risks: Dict[str, float] = {}
        for nid, ndata in TN_NODES.items():
            if ndata["type"] in ["HQ", "Hub"]:
                idx = self.node_to_idx[nid]
                mean_high = float(np.mean([P[idx, 2] for P in timeline_posteriors]))
                hub_risks[nid] = mean_high * (1.2 if ndata["type"] == "HQ" else 1.0)

        vulnerable_hub = max(hub_risks.items(), key=lambda x: x[1])[0]

        edge_disruptions = {
            f"{u}__{v}": data["disruption_prob"]
            for u, v, data in degraded_graph.edges(data=True)
        }
        high_risk_edge = max(edge_disruptions.items(), key=lambda x: x[1])[0]

        # -------------------------------------------------------------------
        # STAGE 7: Jiang et al. (2020) 5 DBN Resilience Capabilities
        # -------------------------------------------------------------------
        # 1. rapid_response (Jiang et al.): Initial posterior reaction velocity
        initial_shift = float(np.mean(np.abs(timeline_posteriors[1] - timeline_posteriors[0])))
        rapid_response = min(1.0, 0.40 + initial_shift * 2.5)

        # 2. sustained_resistance (Jiang et al.): Retention of low delay probability under shock
        max_high_p = float(np.max([np.mean(P[:, 2]) for P in timeline_posteriors]))
        sustained_resistance = max(0.10, 1.0 - max_high_p * 1.5)

        # 3. continuous_running (Jiang et al.): Stability & survival of Pareto-optimal routes
        if primary_solutions:
            best_alpha = primary_solutions[0]["on_time_reliability_alpha"]
            continuous_running = min(1.0, float(best_alpha) * 1.05)
        else:
            continuous_running = 0.30

        # 4. rapid_convergence (Jiang et al.): Recovery rate from peak shock to t_H
        peak_frame = int(np.argmax([np.mean(P[:, 2]) for P in timeline_posteriors]))
        final_high = float(np.mean(timeline_posteriors[-1][:, 2]))
        peak_high = float(np.mean(timeline_posteriors[peak_frame][:, 2]))
        if peak_high > 1e-4:
            rapid_convergence = min(1.0, max(0.20, 1.0 - (final_high / peak_high) * 0.5))
        else:
            rapid_convergence = 0.90

        # 5. dynamic_evolution (Jiang et al.): Trajectory slope and terminal resilience
        dynamic_evolution = round(0.50 * sustained_resistance + 0.50 * rapid_convergence, 3)

        overall_resilience = round(
            0.20 * rapid_response +
            0.25 * sustained_resistance +
            0.20 * continuous_running +
            0.20 * rapid_convergence +
            0.15 * dynamic_evolution,
            3
        )

        scorecard = JiangResilienceScorecard(
            rapid_response=round(rapid_response, 3),
            sustained_resistance=round(sustained_resistance, 3),
            continuous_running=round(continuous_running, 3),
            rapid_convergence=round(rapid_convergence, 3),
            dynamic_evolution=round(dynamic_evolution, 3),
            overall_resilience_index=overall_resilience
        )

        # -------------------------------------------------------------------
        # STAGE 8: Assembly of unified ENGINE_TIMELINE_RESULT JSON payload
        # -------------------------------------------------------------------
        frames: List[TimelineFrame] = []
        seen_undirected = set()
        routes_to_report = []

        for u, v, d in degraded_graph.edges(data=True):
            ekey = tuple(sorted([u, v]))
            if ekey not in seen_undirected:
                seen_undirected.add(ekey)
                op_pct = d["operational_pct"]
                if op_pct < 0.35:
                    status_str = "Severely Disrupted"
                elif op_pct < 0.70:
                    status_str = "Delayed"
                else:
                    status_str = "Normal"

                cid = d.get("corridor_id", "corridor_nh44_central_artery")
                routes_to_report.append(RouteStatus(
                    route_id=f"{u}__{v}",
                    source=u,
                    target=v,
                    corridor_id=cid,
                    corridor_name=d.get("corridor_name", "Transit Corridor"),
                    distance_km=d["distance_km"],
                    travel_time_hr=d["travel_time_hr"],
                    operational_pct=op_pct,
                    status=status_str
                ))

        for t in range(horizon + 1):
            P_t = timeline_posteriors[t]
            node_states = {}
            node_posteriors = {}

            for i, nid in enumerate(self.node_list):
                p_l, p_m, p_h = P_t[i, 0], P_t[i, 1], P_t[i, 2]
                state = "High" if p_h >= 0.40 else ("Medium" if p_m >= 0.35 else "Low")
                node_states[nid] = state
                node_posteriors[nid] = {
                    "Low": round(float(p_l), 3),
                    "Medium": round(float(p_m), 3),
                    "High": round(float(p_h), 3),
                }

            # Macro corridor disruption index
            corridor_disp: Dict[str, float] = {}
            for cid in TAMIL_NADU_CORRIDORS.keys():
                c_links = self.corridor_membership[cid]
                if c_links:
                    c_disr = float(np.mean([degraded_graph[lu][lv]["disruption_prob"] for lu, lv in c_links]))
                else:
                    c_disr = 0.05
                corridor_disp[cid] = round(c_disr, 3)

            mean_high = float(np.mean(P_t[:, 2]))
            net_op_idx = max(0.05, round(1.0 - mean_high, 3))

            frames.append(TimelineFrame(
                time_hour=t,
                node_states=node_states,
                node_posteriors=node_posteriors,
                corridor_disruptions=corridor_disp,
                route_status=routes_to_report,
                cascade_effects=all_cascade_effects[t],
                network_operational_index=net_op_idx
            ))

        total_exec_ms = (time.perf_counter() - t_start) * 1000.0

        return EngineTimelineResult(
            hazard_applied=hazard,
            frames=frames,
            resilience_scorecard=scorecard,
            vulnerable_hub=vulnerable_hub,
            high_risk_edge=high_risk_edge,
            primary_rerouted_solutions=primary_solutions,
            execution_time_ms=round(total_exec_ms, 2),
            network_summary={
                "total_nodes": self.num_nodes,
                "total_edges": degraded_graph.number_of_edges(),
                "total_corridors": len(TAMIL_NADU_CORRIDORS),
                "time_horizon_hours": horizon,
            }
        )
