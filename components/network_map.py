"""
network_map.py — Component 2: Interactive Network Map (PRD 7 §5.2)

Renders the 20-node logistics grid using Plotly Graph Objects.
Color-codes nodes by posterior delay risk P(Delay=High) and highlights
the recommended resilient route.
ZERO imports of networkx or pgmpy.
"""

from __future__ import annotations
from typing import Any
import plotly.graph_objects as go
import streamlit as st


def render_network_map(engine_result: dict[str, Any]) -> None:
    """
    Render the 20-node interactive logistics network map in Plotly.

    Parameters
    ----------
    engine_result : dict
        ENGINE_RESULT dictionary containing posteriors, ranked_routes,
        recommended_route_id, vulnerable_hub, high_risk_edge, and network_graph.
    """
    posteriors = engine_result.get("posteriors", {})
    ranked_routes = engine_result.get("ranked_routes", [])
    recommended_id = engine_result.get("recommended_route_id")
    vulnerable_hub = engine_result.get("vulnerable_hub")
    high_risk_edge_str = engine_result.get("high_risk_edge", "")
    network_graph = engine_result.get("network_graph", {})

    nodes_data = network_graph.get("nodes", [])
    edges_data = network_graph.get("edges", [])

    # Map recommended path edges
    recommended_edges = set()
    recommended_path = []
    if ranked_routes and recommended_id:
        for r in ranked_routes:
            if r.get("route_id") == recommended_id:
                path = r.get("path", [])
                recommended_path = path
                for i in range(len(path) - 1):
                    recommended_edges.add((path[i], path[i + 1]))
                break

    # Parse high risk edge
    risk_edge_tuple = tuple(high_risk_edge_str.split("-")) if "-" in high_risk_edge_str else ()

    # Create node lookup
    node_positions = {n["id"]: n["pos"] for n in nodes_data}
    node_types = {n["id"]: n.get("type", "hub") for n in nodes_data}

    fig = go.Figure()

    # 1. Base Edges Trace (Subtle grey)
    edge_x = []
    edge_y = []
    for edge in edges_data:
        u, v = edge["source"], edge["target"]
        if (u, v) in recommended_edges or (u, v) == risk_edge_tuple:
            continue  # drawn separately with custom styling
        if u in node_positions and v in node_positions:
            x0, y0 = node_positions[u]
            x1, y1 = node_positions[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="#cbd5e1", width=1.5),
            hoverinfo="none",
            showlegend=False,
            name="Network Edge",
        )
    )

    # 2. High Risk Edge Trace (Dashed Crimson)
    if len(risk_edge_tuple) == 2 and risk_edge_tuple[0] in node_positions and risk_edge_tuple[1] in node_positions:
        u, v = risk_edge_tuple
        x0, y0 = node_positions[u]
        x1, y1 = node_positions[v]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color="#ef4444", width=3.5, dash="dash"),
                hoverinfo="text",
                hovertext=f"High Risk Edge: {u} &rarr; {v}",
                showlegend=True,
                name="Flagged Chokepoint Edge",
            )
        )

    # 3. Recommended Route Edges Trace (Vibrant Green)
    rec_edge_x = []
    rec_edge_y = []
    for u, v in recommended_edges:
        if u in node_positions and v in node_positions:
            x0, y0 = node_positions[u]
            x1, y1 = node_positions[v]
            rec_edge_x.extend([x0, x1, None])
            rec_edge_y.extend([y0, y1, None])

    if rec_edge_x:
        fig.add_trace(
            go.Scatter(
                x=rec_edge_x,
                y=rec_edge_y,
                mode="lines",
                line=dict(color="#10b981", width=4.5),
                hoverinfo="text",
                hovertext=f"Recommended Path ({recommended_id})",
                showlegend=True,
                name="Recommended Route",
            )
        )

    # 4. Hub Nodes (Categorized by delay risk)
    node_x = []
    node_y = []
    node_colors = []
    node_texts = []
    node_symbols = []
    node_sizes = []
    node_borders = []

    for node in nodes_data:
        nid = node["id"]
        if nid not in node_positions:
            continue
        x, y = node_positions[nid]
        ntype = node_types.get(nid, "hub")

        # Find posterior delay probabilities
        p_high = 0.0
        p_med = 0.0
        p_low = 1.0

        for key, probs in posteriors.items():
            if nid in key and "Delay" in key:
                p_high = probs.get("High", 0.0)
                p_med = probs.get("Medium", 0.0)
                p_low = probs.get("Low", 0.0)
                break

        # Color mapping based on P(High)
        if ntype == "warehouse":
            color = "#0284c7"
            symbol = "diamond"
            size = 24
            border_color = "#0369a1"
            border_width = 2
            risk_label = "Origin Facility"
        elif ntype == "delivery_zone":
            color = "#7c3aed"
            symbol = "star"
            size = 26
            border_color = "#6d28d9"
            border_width = 2
            risk_label = "Destination Delivery Target"
        else:
            symbol = "circle"
            size = 20
            if p_high > 0.50:
                color = "#ef4444"  # Red
                border_color = "#991b1b"
                border_width = 3 if nid == vulnerable_hub else 1.5
                risk_label = "High Disruption Risk"
            elif p_high > 0.25:
                color = "#f59e0b"  # Amber
                border_color = "#b45309"
                border_width = 2 if nid == vulnerable_hub else 1
                risk_label = "Moderate Delay Risk"
            else:
                color = "#10b981"  # Green
                border_color = "#047857"
                border_width = 2 if nid == vulnerable_hub else 1
                risk_label = "Nominal Low Delay"

        if nid == vulnerable_hub:
            risk_label += " (MOST VULNERABLE HUB)"
            size = 26

        hover_html = (
            f"<b>{nid}</b> ({risk_label})<br>"
            f"P(Delay=Low): {p_low*100:.1f}%<br>"
            f"P(Delay=Med): {p_med*100:.1f}%<br>"
            f"P(Delay=High): <b>{p_high*100:.1f}%</b>"
        )

        node_x.append(x)
        node_y.append(y)
        node_colors.append(color)
        node_symbols.append(symbol)
        node_sizes.append(size)
        node_texts.append(hover_html)
        node_borders.append(border_color)

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                symbol=node_symbols,
                line=dict(width=2, color=node_borders),
            ),
            text=[n["id"] for n in nodes_data],
            textposition="top center",
            textfont=dict(size=10, color="#1e293b", family="sans-serif"),
            hoverinfo="text",
            hovertext=node_texts,
            showlegend=False,
            name="Network Nodes",
        )
    )

    # Figure Layout
    fig.update_layout(
        title=dict(
            text="<b>Logistics Network Topology & Stochastic Delay Heatmap</b>",
            x=0.02,
            font=dict(size=14, color="#1e293b"),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=40, b=20),
        height=520,
    )

    st.plotly_chart(fig, use_container_width=True)
