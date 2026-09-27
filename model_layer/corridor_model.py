"""
corridor_model.py — Pipeline Stage 2: Uncertainty Modeling (path-centric)

Groups edges sharing a common disruption source into *corridors*, replacing
the naive assumption that every edge's delay is independent.

Technique: SPOTAR / PACE path-centric dependency model, Andonov & Yang
(PRD 1 §3.2).  This is a lightweight approximation: rather than full
trajectory-level modeling, we group edges that plausibly share the same
disruption exposure (same weather cell, same downstream congestion).

Known limitation (documented, not an oversight):
    Each edge is assigned to exactly ONE corridor.  Edges that could
    plausibly belong to overlapping corridors (e.g. same-row weather
    exposure AND shared downstream-hub congestion) are assigned to
    whichever corridor is defined first.  This is a modeling simplification
    acceptable for the 20-node grid; a production system would use a
    many-to-many mapping.
"""

from __future__ import annotations
import networkx as nx


def define_corridors(G: nx.DiGraph) -> dict[str, list[tuple[str, str]]]:
    """
    Define corridor groups from the graph's grid structure.

    Grouping heuristic:
      1. **Row corridors** — all horizontal edges in the same grid row share
         weather-cell exposure (e.g. a storm covering the entire northern tier).
      2. **Column corridors** — all vertical edges in the same grid column
         share congestion-source exposure (packages flowing through the same
         downstream sorting chain).
      3. **Entry/exit corridors** — Warehouse-to-row-0 and row-5-to-DeliveryZone
         edges are grouped separately (single-point-of-failure exposure).

    Parameters
    ----------
    G : nx.DiGraph
        The logistics graph from graph_builder.build_logistics_graph().

    Returns
    -------
    dict[str, list[tuple[str, str]]]
        {corridor_id: [(src, dst), ...]}
    """
    corridors: dict[str, list[tuple[str, str]]] = {}

    # Collect grid metadata
    hub_data = {}
    for node, data in G.nodes(data=True):
        if data.get("node_type") == "hub":
            hub_data[node] = (data["grid_row"], data["grid_col"])

    # 1. Row corridors: horizontal edges in the same row
    for (src, dst) in G.edges():
        if src in hub_data and dst in hub_data:
            src_row, src_col = hub_data[src]
            dst_row, dst_col = hub_data[dst]
            if src_row == dst_row:  # same row = horizontal edge
                cid = f"row_{src_row}_weather"
                corridors.setdefault(cid, []).append((src, dst))

    # 2. Column corridors: vertical edges in the same column
    for (src, dst) in G.edges():
        if src in hub_data and dst in hub_data:
            src_row, src_col = hub_data[src]
            dst_row, dst_col = hub_data[dst]
            if src_col == dst_col and abs(src_row - dst_row) == 1:
                cid = f"col_{src_col}_congestion"
                corridors.setdefault(cid, []).append((src, dst))

    # 3. Diagonal corridors: diagonal edges grouped by direction
    for (src, dst) in G.edges():
        if src in hub_data and dst in hub_data:
            src_row, src_col = hub_data[src]
            dst_row, dst_col = hub_data[dst]
            if abs(src_row - dst_row) == 1 and abs(src_col - dst_col) == 1:
                direction = "right" if dst_col > src_col else "left"
                cid = f"diag_{direction}_cross"
                corridors.setdefault(cid, []).append((src, dst))

    # 4. Entry corridor: Warehouse → row 0
    entry_edges = [(s, d) for s, d in G.edges() if s == "Warehouse"]
    if entry_edges:
        corridors["entry_warehouse"] = entry_edges

    # 5. Exit corridor: row 5 → DeliveryZone
    exit_edges = [(s, d) for s, d in G.edges() if d == "DeliveryZone"]
    if exit_edges:
        corridors["exit_delivery"] = exit_edges

    return corridors


def assign_corridor_ids(G: nx.DiGraph, corridors: dict[str, list[tuple[str, str]]]) -> None:
    """
    Mutate G in place, setting edge['corridor_id'] for every edge.

    Each edge is assigned to the FIRST corridor it appears in.  Edges that
    appear in no corridor (shouldn't happen with the full heuristic above,
    but guarded against) get corridor_id = "uncorridored".

    Parameters
    ----------
    G : nx.DiGraph
        The logistics graph (mutated in place).
    corridors : dict
        Output of define_corridors().
    """
    # Build reverse map: edge -> first corridor
    edge_to_corridor: dict[tuple[str, str], str] = {}
    for cid, edges in corridors.items():
        for edge in edges:
            if edge not in edge_to_corridor:
                edge_to_corridor[edge] = cid

    for (src, dst) in G.edges():
        G[src][dst]["corridor_id"] = edge_to_corridor.get(
            (src, dst), "uncorridored"
        )


def get_corridor_edges(G: nx.DiGraph, corridor_id: str) -> list[tuple[str, str]]:
    """Return all edges in G that belong to the given corridor."""
    return [
        (s, d) for s, d, data in G.edges(data=True)
        if data.get("corridor_id") == corridor_id
    ]


def get_all_corridor_ids(G: nx.DiGraph) -> list[str]:
    """Return sorted list of unique corridor IDs assigned in the graph."""
    return sorted({
        data["corridor_id"]
        for _, _, data in G.edges(data=True)
        if data.get("corridor_id") is not None
    })
