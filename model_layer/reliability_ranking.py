"""
reliability_ranking.py — Pipeline Stage 6: Reliability Ranking

Implements Chen et al.'s (2012) label-setting and A* algorithms with
first-order stochastic dominance (FSD) pruning.

This is the project's hand-written algorithmic contribution — NOT available
in networkx or pgmpy.

Key concepts:
    - A *label* at node n encodes: (n, cumulative_time_budget, on_time_probability, path).
    - Label A *dominates* label B (FSD) if A reaches the same node with
      time_budget ≤ B's AND on_time_prob ≥ B's, with at least one strict
      inequality.
    - Dominated labels are pruned during search, avoiding exponential
      path enumeration (Mirchandani's original approach, cited as unusable
      at scale by Chen et al.).

Complexity note:
    The 20-node grid is small enough that either variant runs in well under
    a second, but implementing the pruning demonstrates the algorithmic
    contribution rather than a brute-force stand-in.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
import heapq

import networkx as nx


@dataclass
class Label:
    """
    A label at a node in the RSPP search.

    Attributes
    ----------
    node : str
        Current node.
    cumulative_time_budget : float
        Total travel-time budget consumed to reach this node.
    on_time_probability : float
        Probability of on-time arrival along this partial path.
    path : list[str]
        Ordered list of nodes visited.
    route_id : str
        Identifier for this route (assigned after search completes).
    """
    node: str
    cumulative_time_budget: float
    on_time_probability: float
    path: list[str] = field(default_factory=list)
    route_id: str = ""

    def __lt__(self, other: "Label") -> bool:
        """For heapq ordering — prefer higher on_time_probability."""
        return self.on_time_probability > other.on_time_probability


def dominates(label_a: Label, label_b: Label) -> bool:
    """
    First-order stochastic dominance (FSD) check per Chen et al. 2012.

    label_a dominates label_b if:
      1. They are at the same node.
      2. label_a.time_budget <= label_b.time_budget
      3. label_a.on_time_prob >= label_b.on_time_prob
      4. At least one inequality is strict.

    Returns True if label_a dominates label_b (i.e. label_b can be pruned).
    """
    if label_a.node != label_b.node:
        return False

    time_le = label_a.cumulative_time_budget <= label_b.cumulative_time_budget
    prob_ge = label_a.on_time_probability >= label_b.on_time_probability

    if not (time_le and prob_ge):
        return False

    # At least one strict inequality
    strict_time = label_a.cumulative_time_budget < label_b.cumulative_time_budget
    strict_prob = label_a.on_time_probability > label_b.on_time_probability

    return strict_time or strict_prob


def _is_dominated(label: Label, label_set: list[Label]) -> bool:
    """Check if label is dominated by any label in label_set."""
    return any(dominates(existing, label) for existing in label_set)


def _prune_dominated(label_set: list[Label]) -> list[Label]:
    """Remove all labels dominated by another label in the set."""
    non_dominated = []
    for label in label_set:
        if not any(dominates(other, label) for other in label_set if other is not label):
            non_dominated.append(label)
    return non_dominated


def _edge_on_time_prob(
    G: nx.DiGraph,
    src: str,
    dst: str,
    posteriors: dict[str, dict[str, float]],
) -> float:
    """
    Compute the probability of traversing edge (src, dst) without excessive delay.

    Uses the posterior delay probabilities from BN inference:
    P(on_time for edge) = P(Delay=Low at dst) + P(Delay=Medium at dst)
    i.e. 1 - P(Delay=High at dst).

    Falls back to (1 - base_disruption_prob) if no posterior data available.
    """
    # Try to find a posterior for the destination hub's delay
    delay_key = f"{dst}_Delay_t0"
    if delay_key in posteriors:
        return 1.0 - posteriors[delay_key].get("High", 0.0)

    # Try without time slice suffix
    if dst in posteriors:
        return 1.0 - posteriors[dst].get("High", 0.0)

    # Fallback to base disruption probability
    if G.has_edge(src, dst):
        return 1.0 - G[src][dst].get("base_disruption_prob", 0.05)

    return 0.95  # default


def rspp_ls(
    G: nx.DiGraph,
    source: str,
    target: str,
    time_budget: float,
    posteriors: dict[str, dict[str, float]] | None = None,
    max_candidates: int = 40,
) -> list[Label]:
    """
    Multi-criteria label-setting algorithm (RSPP-LS).

    Maintains a set of non-dominated labels at every node; discards any
    label that is dominated per `dominates()` above.

    Theorem 1 (Chen et al. 2012): a sub-path of a non-dominated path is
    itself non-dominated — so pruning during expansion is safe.

    Parameters
    ----------
    G : nx.DiGraph
        Logistics graph with edge attributes.
    source : str
        Start node (typically "Warehouse").
    target : str
        End node (typically "DeliveryZone").
    time_budget : float
        Maximum allowed cumulative travel time.
    posteriors : dict or None
        {node_name: {"Low": p, "Medium": p, "High": p}} from BN inference.
    max_candidates : int
        Safety cap on total labels generated (prevents runaway on dense graphs).

    Returns
    -------
    list[Label]
        Non-dominated labels that reach `target`, sorted by on_time_probability
        descending.
    """
    if posteriors is None:
        posteriors = {}

    # Label sets per node
    node_labels: dict[str, list[Label]] = {n: [] for n in G.nodes()}

    # Initial label at source
    start_label = Label(
        node=source,
        cumulative_time_budget=0.0,
        on_time_probability=1.0,
        path=[source],
    )
    node_labels[source] = [start_label]

    # Queue: labels to expand
    queue = [start_label]
    total_generated = 0

    while queue and total_generated < max_candidates * 10:
        current = queue.pop(0)

        for _, neighbor, edge_data in G.edges(current.node, data=True):
            # Skip if already visited on this path (no cycles)
            if neighbor in current.path:
                continue

            travel_time = edge_data.get("base_travel_time", 20.0)
            new_budget = current.cumulative_time_budget + travel_time

            # Prune: exceeds time budget
            if new_budget > time_budget:
                continue

            # Compute on-time probability for this extension
            edge_prob = _edge_on_time_prob(G, current.node, neighbor, posteriors)
            new_prob = current.on_time_probability * edge_prob

            new_label = Label(
                node=neighbor,
                cumulative_time_budget=new_budget,
                on_time_probability=new_prob,
                path=current.path + [neighbor],
            )
            total_generated += 1

            # Dominance check: is this new label dominated?
            if _is_dominated(new_label, node_labels[neighbor]):
                continue

            # Remove labels this new one dominates
            node_labels[neighbor] = [
                l for l in node_labels[neighbor]
                if not dominates(new_label, l)
            ]
            node_labels[neighbor].append(new_label)

            # Only expand further if not at target
            if neighbor != target:
                queue.append(new_label)

    # Collect non-dominated labels at target
    result = _prune_dominated(node_labels.get(target, []))
    result.sort(key=lambda l: l.on_time_probability, reverse=True)

    # Assign route IDs
    for i, label in enumerate(result):
        label.route_id = f"R{i + 1}"

    return result


def rspp_astar(
    G: nx.DiGraph,
    source: str,
    target: str,
    time_budget: float,
    posteriors: dict[str, dict[str, float]] | None = None,
    heuristic: Callable[[str, str], float] | None = None,
    max_candidates: int = 40,
) -> list[Label]:
    """
    RSPP-A* — same dominance logic as rspp_ls, but prioritizes expansion
    of labels closer to `target` using a heuristic.

    Chen et al. (2012) report 20–50% speedup over RSPP-LS on large networks.

    Parameters
    ----------
    G : nx.DiGraph
        Logistics graph.
    source, target : str
        Start and end nodes.
    time_budget : float
        Maximum cumulative travel time.
    posteriors : dict or None
        BN inference results.
    heuristic : callable or None
        h(node, target) -> estimated remaining time.  If None, uses grid
        distance from node positions.
    max_candidates : int
        Safety cap.

    Returns
    -------
    list[Label]
        Non-dominated labels at target, sorted by on_time_probability desc.
    """
    if posteriors is None:
        posteriors = {}

    if heuristic is None:
        heuristic = _grid_heuristic(G)

    node_labels: dict[str, list[Label]] = {n: [] for n in G.nodes()}

    start_label = Label(
        node=source,
        cumulative_time_budget=0.0,
        on_time_probability=1.0,
        path=[source],
    )
    node_labels[source] = [start_label]

    # Priority queue: (priority, label)
    # Priority = cumulative_time + heuristic estimate (lower = better)
    counter = 0
    pq: list[tuple[float, int, Label]] = []
    h_start = heuristic(source, target)
    heapq.heappush(pq, (h_start, counter, start_label))
    counter += 1

    total_generated = 0

    while pq and total_generated < max_candidates * 10:
        _, _, current = heapq.heappop(pq)

        # Skip if this label was since dominated
        if _is_dominated(current, node_labels[current.node]):
            continue

        if current.node == target:
            continue  # already at target, no expansion needed

        for _, neighbor, edge_data in G.edges(current.node, data=True):
            if neighbor in current.path:
                continue

            travel_time = edge_data.get("base_travel_time", 20.0)
            new_budget = current.cumulative_time_budget + travel_time

            if new_budget > time_budget:
                continue

            edge_prob = _edge_on_time_prob(G, current.node, neighbor, posteriors)
            new_prob = current.on_time_probability * edge_prob

            new_label = Label(
                node=neighbor,
                cumulative_time_budget=new_budget,
                on_time_probability=new_prob,
                path=current.path + [neighbor],
            )
            total_generated += 1

            if _is_dominated(new_label, node_labels[neighbor]):
                continue

            node_labels[neighbor] = [
                l for l in node_labels[neighbor]
                if not dominates(new_label, l)
            ]
            node_labels[neighbor].append(new_label)

            if neighbor != target:
                priority = new_budget + heuristic(neighbor, target)
                heapq.heappush(pq, (priority, counter, new_label))
                counter += 1

    result = _prune_dominated(node_labels.get(target, []))
    result.sort(key=lambda l: l.on_time_probability, reverse=True)

    for i, label in enumerate(result):
        label.route_id = f"R{i + 1}"

    return result


def _grid_heuristic(G: nx.DiGraph) -> Callable[[str, str], float]:
    """
    Build a heuristic function using Manhattan-like grid distance.

    Returns a callable h(node, target) -> estimated remaining time.
    """
    positions = {}
    for n, data in G.nodes(data=True):
        if "pos" in data:
            positions[n] = data["pos"]

    def h(node: str, target: str) -> float:
        if node not in positions or target not in positions:
            return 0.0
        x1, y1 = positions[node]
        x2, y2 = positions[target]
        # Use Manhattan distance scaled by minimum travel time
        dist = abs(x2 - x1) + abs(y2 - y1)
        return dist * 5.0  # rough scaling to travel-time units

    return h


def compute_reliability_score(label: Label, max_time: float = 200.0) -> float:
    """
    Compute a composite reliability score for a route label.

    Combines on_time_probability (weight 0.7) with time efficiency
    (weight 0.3) into a single [0, 1] score.

    Parameters
    ----------
    label : Label
        A completed route label from RSPP search.
    max_time : float
        Normalization constant for time efficiency.

    Returns
    -------
    float
        Reliability score in [0, 1].
    """
    time_efficiency = max(0, 1.0 - label.cumulative_time_budget / max_time)
    return 0.7 * label.on_time_probability + 0.3 * time_efficiency


def label_to_dict(label: Label, max_time: float = 200.0) -> dict:
    """Convert a Label to the route dict format expected by ENGINE_RESULT."""
    return {
        "route_id": label.route_id,
        "path": label.path,
        "on_time_probability": round(label.on_time_probability, 4),
        "reliability_score": round(compute_reliability_score(label, max_time), 4),
        "cumulative_time": round(label.cumulative_time_budget, 1),
        "dominated": False,
    }
