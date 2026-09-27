"""
graph_builder.py — Pipeline Stage 1: Network Definition

Builds the 20+ node directed logistics graph:
  - 1 Warehouse (origin)
  - 18 regional/sorting hubs arranged in a 6×3 grid
  - 1 DeliveryZone (destination)

Each edge carries:
  - base_travel_time (float, minutes)
  - base_disruption_prob (float, 0..1)
  - corridor_id (str | None, set later by corridor_model.py)

Technique: Chen et al. (2012) node/link/α-reliable-path notation (PRD 1 §3.1).
"""

import networkx as nx


# ---------------------------------------------------------------------------
# Grid layout constants
# ---------------------------------------------------------------------------
# The 18 hubs are arranged in a 6-row × 3-column grid.
# Row 0 (top) connects to the Warehouse; Row 5 (bottom) connects to DeliveryZone.
#
#   Warehouse
#      |  \   \
#   H1  H2  H3      <- row 0
#   H4  H5  H6      <- row 1
#   H7  H8  H9      <- row 2
#   H10 H11 H12     <- row 3
#   H13 H14 H15     <- row 4
#   H16 H17 H18     <- row 5
#      |  /   /
#   DeliveryZone

GRID_ROWS = 6
GRID_COLS = 3


def _hub_name(row: int, col: int) -> str:
    """Convert grid (row, col) to hub name, e.g. (0,0) -> 'Hub1'."""
    return f"Hub{row * GRID_COLS + col + 1}"


def _hub_pos(row: int, col: int) -> tuple[float, float]:
    """Return (x, y) position for visualization.  y=0 is top."""
    return (col * 2.0, -row * 2.0)


# ---------------------------------------------------------------------------
# Risk assignment
# ---------------------------------------------------------------------------
# Hubs that the baseline PPT marks as high-risk or high-congestion.
# These are deliberately placed at chokepoints in the grid.
HIGH_CONGESTION_HUBS = {"Hub5", "Hub8", "Hub14"}     # mid-column bottlenecks
HIGH_RISK_HUBS = {"Hub4", "Hub11"}                    # left-column weather-exposed


def _node_risk(name: str) -> str:
    if name in HIGH_CONGESTION_HUBS:
        return "high_congestion"
    if name in HIGH_RISK_HUBS:
        return "high_risk"
    return "normal"


# ---------------------------------------------------------------------------
# Base travel times and disruption probabilities
# ---------------------------------------------------------------------------
# Travel times (minutes) and disruption probabilities are seeded with
# plausible values per the baseline PPT.  Horizontal edges (same row,
# adjacent column) are shorter than vertical edges (same column, next row),
# reflecting that intra-region transfers are faster than inter-region hops.

_HORIZONTAL_TRAVEL_TIME = 15.0   # minutes
_VERTICAL_TRAVEL_TIME = 25.0     # minutes
_DIAGONAL_TRAVEL_TIME = 30.0     # minutes
_ENTRY_EXIT_TRAVEL_TIME = 20.0   # Warehouse/DeliveryZone connections

# Base disruption probability for normal edges; higher for edges touching
# high-risk or high-congestion hubs.
_BASE_DISRUPTION = 0.05
_HIGH_DISRUPTION = 0.15
_CONGESTION_DISRUPTION = 0.12


def _edge_disruption_prob(src: str, dst: str) -> float:
    """Higher disruption probability if either endpoint is high-risk."""
    if src in HIGH_RISK_HUBS or dst in HIGH_RISK_HUBS:
        return _HIGH_DISRUPTION
    if src in HIGH_CONGESTION_HUBS or dst in HIGH_CONGESTION_HUBS:
        return _CONGESTION_DISRUPTION
    return _BASE_DISRUPTION


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_logistics_graph() -> nx.DiGraph:
    """
    Build and return the 20-node directed logistics graph.

    Returns
    -------
    nx.DiGraph
        Directed graph with ≥20 nodes and edge attributes:
        base_travel_time, base_disruption_prob, corridor_id.
    """
    G = nx.DiGraph()

    # --- Add Warehouse and DeliveryZone ---
    G.add_node("Warehouse", node_type="warehouse", risk_level="normal",
               pos=(2.0, 2.0))
    G.add_node("DeliveryZone", node_type="delivery_zone", risk_level="normal",
               pos=(2.0, -(GRID_ROWS * 2.0 + 1)))

    # --- Add 18 hub nodes (6 rows × 3 cols) ---
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            name = _hub_name(r, c)
            G.add_node(name,
                       node_type="hub",
                       risk_level=_node_risk(name),
                       grid_row=r,
                       grid_col=c,
                       pos=_hub_pos(r, c))

    # --- Warehouse → Row 0 ---
    for c in range(GRID_COLS):
        dst = _hub_name(0, c)
        G.add_edge("Warehouse", dst,
                   base_travel_time=_ENTRY_EXIT_TRAVEL_TIME,
                   base_disruption_prob=_edge_disruption_prob("Warehouse", dst),
                   corridor_id=None)

    # --- Vertical edges: row r → row r+1 (same column) ---
    for r in range(GRID_ROWS - 1):
        for c in range(GRID_COLS):
            src = _hub_name(r, c)
            dst = _hub_name(r + 1, c)
            G.add_edge(src, dst,
                       base_travel_time=_VERTICAL_TRAVEL_TIME,
                       base_disruption_prob=_edge_disruption_prob(src, dst),
                       corridor_id=None)

    # --- Horizontal edges: same row, adjacent columns (bidirectional) ---
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS - 1):
            src = _hub_name(r, c)
            dst = _hub_name(r, c + 1)
            G.add_edge(src, dst,
                       base_travel_time=_HORIZONTAL_TRAVEL_TIME,
                       base_disruption_prob=_edge_disruption_prob(src, dst),
                       corridor_id=None)
            G.add_edge(dst, src,
                       base_travel_time=_HORIZONTAL_TRAVEL_TIME,
                       base_disruption_prob=_edge_disruption_prob(dst, src),
                       corridor_id=None)

    # --- Diagonal edges: row r, col c → row r+1, col c±1 ---
    # These add hub-and-spoke style connectivity (more realistic than a
    # pure grid, and directly addresses the RDBN airline paper's topology
    # limitation — PRD 1 §3.6).
    for r in range(GRID_ROWS - 1):
        for c in range(GRID_COLS):
            src = _hub_name(r, c)
            if c + 1 < GRID_COLS:
                dst = _hub_name(r + 1, c + 1)
                G.add_edge(src, dst,
                           base_travel_time=_DIAGONAL_TRAVEL_TIME,
                           base_disruption_prob=_edge_disruption_prob(src, dst),
                           corridor_id=None)
            if c - 1 >= 0:
                dst = _hub_name(r + 1, c - 1)
                G.add_edge(src, dst,
                           base_travel_time=_DIAGONAL_TRAVEL_TIME,
                           base_disruption_prob=_edge_disruption_prob(src, dst),
                           corridor_id=None)

    # --- Row 5 → DeliveryZone ---
    for c in range(GRID_COLS):
        src = _hub_name(GRID_ROWS - 1, c)
        G.add_edge(src, "DeliveryZone",
                   base_travel_time=_ENTRY_EXIT_TRAVEL_TIME,
                   base_disruption_prob=_edge_disruption_prob(src, "DeliveryZone"),
                   corridor_id=None)

    return G


def get_all_hub_names() -> list[str]:
    """Return ordered list of hub names Hub1..Hub18."""
    return [_hub_name(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)]


def get_node_positions(G: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Return {node_name: (x, y)} for visualization."""
    return {n: d["pos"] for n, d in G.nodes(data=True)}
