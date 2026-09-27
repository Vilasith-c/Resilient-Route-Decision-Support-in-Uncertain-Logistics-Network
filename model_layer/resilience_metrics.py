"""
resilience_metrics.py — Pipeline Stage 7: Resilience Scoring

Computes the five DBN resilience capabilities from Jiang et al. (PRD 1 §3.5),
adapted from the computer-network domain to the physical logistics domain.

Five capabilities:
    1. rapid_response — how quickly delay-state probabilities react to evidence
    2. sustained_resistance — how much on-time probability degrades under
       sustained disruption
    3. continuous_running — fraction of routes remaining non-dominated
    4. rapid_convergence — how quickly posteriors return to baseline after
       disruption clears
    5. dynamic_evolution — overall trend of network reliability across time

Also provides vulnerability identification:
    - Most vulnerable hub (highest weighted delay risk contribution)
    - Highest-risk edge (highest weighted disruption exposure)
"""

from __future__ import annotations

import networkx as nx
import numpy as np


# ---------------------------------------------------------------------------
# Resilience capability computations
# ---------------------------------------------------------------------------

def compute_resilience_scorecard(
    posteriors_over_time: list[dict[str, dict[str, float]]],
) -> dict[str, float]:
    """
    Given a sequence of posterior snapshots across time slices, compute
    the five resilience capabilities.

    Parameters
    ----------
    posteriors_over_time : list[dict]
        List of posterior dictionaries, one per time step.
        Each dict maps node_name -> {"Low": p, "Medium": p, "High": p}.

    Returns
    -------
    dict[str, float]
        Five resilience scores, each in [0, 1].
    """
    if not posteriors_over_time:
        return {
            "rapid_response": 0.5,
            "sustained_resistance": 0.5,
            "continuous_running": 0.5,
            "rapid_convergence": 0.5,
            "dynamic_evolution": 0.5,
        }

    n_steps = len(posteriors_over_time)

    # Extract delay-node average P(High) per time step
    high_probs_per_step = []
    for posteriors in posteriors_over_time:
        delay_nodes = [k for k in posteriors if "Delay" in k]
        if delay_nodes:
            avg_high = np.mean([
                posteriors[k].get("High", 0.0) for k in delay_nodes
            ])
        else:
            avg_high = 0.1
        high_probs_per_step.append(avg_high)

    # 1. Rapid Response: how quickly the network reacts to evidence
    #    Measured as the magnitude of the first posterior shift
    if n_steps >= 2:
        initial_shift = abs(high_probs_per_step[1] - high_probs_per_step[0])
        rapid_response = min(1.0, initial_shift / 0.3)  # normalize
    else:
        rapid_response = 0.5

    # 2. Sustained Resistance: how well on-time probability holds up
    #    Lower average P(High) across time = better resistance
    avg_high_overall = np.mean(high_probs_per_step)
    sustained_resistance = max(0.0, 1.0 - avg_high_overall)

    # 3. Continuous Running: stability of the network across time steps
    #    Lower variance in P(High) across time = more continuous
    if n_steps >= 2:
        variance = np.var(high_probs_per_step)
        continuous_running = max(0.0, 1.0 - variance * 10)  # scale variance
    else:
        continuous_running = 0.5

    # 4. Rapid Convergence: how quickly posteriors recover after peak disruption
    #    If the last step's P(High) is lower than the peak, that's convergence
    if n_steps >= 3:
        peak_idx = np.argmax(high_probs_per_step)
        if peak_idx < n_steps - 1:
            peak_val = high_probs_per_step[peak_idx]
            final_val = high_probs_per_step[-1]
            recovery = (peak_val - final_val) / max(peak_val, 0.01)
            rapid_convergence = max(0.0, min(1.0, recovery))
        else:
            rapid_convergence = 0.3  # still at peak, hasn't recovered
    else:
        rapid_convergence = 0.5

    # 5. Dynamic Evolution: overall trend — is the network getting more reliable?
    #    Negative slope in P(High) over time = improving = higher score
    if n_steps >= 2:
        x = np.arange(n_steps, dtype=float)
        slope = np.polyfit(x, high_probs_per_step, 1)[0]
        dynamic_evolution = max(0.0, min(1.0, 0.5 - slope * 5))
    else:
        dynamic_evolution = 0.5

    return {
        "rapid_response": round(float(rapid_response), 4),
        "sustained_resistance": round(float(sustained_resistance), 4),
        "continuous_running": round(float(continuous_running), 4),
        "rapid_convergence": round(float(rapid_convergence), 4),
        "dynamic_evolution": round(float(dynamic_evolution), 4),
    }


# ---------------------------------------------------------------------------
# Vulnerability identification
# ---------------------------------------------------------------------------

def identify_vulnerable_hub(
    G: nx.DiGraph,
    posteriors: dict[str, dict[str, float]],
) -> str:
    """
    Identify the hub with the highest weighted contribution to route delay risk.

    Scoring heuristic:
        vulnerability(hub) = P(Delay=High) * degree(hub) / max_degree

    Higher degree hubs are more critical because their disruption propagates
    to more routes.

    Parameters
    ----------
    G : nx.DiGraph
        Logistics graph.
    posteriors : dict
        Current posterior probabilities.

    Returns
    -------
    str
        Name of the most vulnerable hub.
    """
    hub_scores: dict[str, float] = {}

    # Get all hub nodes from the graph
    hub_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "hub"]
    if not hub_nodes:
        return "Unknown"

    max_degree = max(G.degree(n) for n in hub_nodes)
    if max_degree == 0:
        max_degree = 1

    for hub in hub_nodes:
        # Find the corresponding delay posterior
        p_high = 0.0
        for key in posteriors:
            if hub in key and "Delay" in key:
                p_high = posteriors[key].get("High", 0.0)
                break

        degree_factor = G.degree(hub) / max_degree
        hub_scores[hub] = p_high * degree_factor

    if not hub_scores:
        return hub_nodes[0]

    return max(hub_scores, key=hub_scores.get)


def identify_high_risk_edge(
    G: nx.DiGraph,
    posteriors: dict[str, dict[str, float]],
) -> tuple[str, str]:
    """
    Identify the edge with the highest weighted contribution to route delay risk.

    Scoring heuristic:
        risk(edge) = (P(Delay_High at src) + P(Delay_High at dst)) / 2
                     * base_disruption_prob

    Parameters
    ----------
    G : nx.DiGraph
        Logistics graph.
    posteriors : dict
        Current posterior probabilities.

    Returns
    -------
    tuple[str, str]
        (src, dst) of the highest-risk edge.
    """
    edge_scores: dict[tuple[str, str], float] = {}

    for src, dst, data in G.edges(data=True):
        p_high_src = 0.0
        p_high_dst = 0.0

        for key in posteriors:
            if src in key and "Delay" in key:
                p_high_src = posteriors[key].get("High", 0.0)
            if dst in key and "Delay" in key:
                p_high_dst = posteriors[key].get("High", 0.0)

        base_disruption = data.get("base_disruption_prob", 0.05)
        avg_delay = (p_high_src + p_high_dst) / 2.0
        edge_scores[(src, dst)] = avg_delay * base_disruption + base_disruption

    if not edge_scores:
        edges = list(G.edges())
        return edges[0] if edges else ("Unknown", "Unknown")

    return max(edge_scores, key=edge_scores.get)


def format_edge_name(edge: tuple[str, str]) -> str:
    """Format edge tuple as 'Hub4-Hub5' string for display."""
    return f"{edge[0]}-{edge[1]}"
