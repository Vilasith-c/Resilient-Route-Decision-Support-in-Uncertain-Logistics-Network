"""
report_generator.py — Pipeline Stage 8: Report Generation (PRD 6 §6)

Renders an ENGINE_RESULT dictionary into an executive Probabilistic Logistics
Resilience Report in PDF format using ReportLab.
"""

from __future__ import annotations
import io
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_report(engine_result: dict[str, Any]) -> bytes:
    """
    Builds an executive PDF report containing:
      - Header & Run Metadata (timestamp, time slice, active evidence)
      - Recommended Route with plain-language justification
      - Top Ranked Routes Comparison Table (on-time probability, reliability score, travel time)
      - Resilience Capabilities Scorecard (5 metrics from Jiang et al.)
      - Critical Vulnerabilities (vulnerable hub & high-risk corridor edge)

    Parameters
    ----------
    engine_result : dict
        Output from update_evidence().

    Returns
    -------
    bytes
        Raw PDF bytes for Streamlit's download button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0369a1"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    elements = []

    # Title & Metadata
    elements.append(Paragraph("Probabilistic Logistics Resilience Report", title_style))
    elements.append(
        Paragraph(
            "Bayesian Dynamic Network Decision Support & Stochastic Route Reliability",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

    timestamp = engine_result.get("timestamp", "N/A")
    time_slice = engine_result.get("time_slice", 0)
    evidence = engine_result.get("evidence_applied", {})
    evidence_str = (
        ", ".join([f"<b>{k}</b>: {v}" for k, v in evidence.items()])
        if evidence
        else "<i>Baseline (no disruptions injected)</i>"
    )

    meta_text = (
        f"<b>Generated At:</b> {timestamp} &nbsp;|&nbsp; "
        f"<b>Time Slice:</b> t = {time_slice} hr<br/>"
        f"<b>Active Evidence:</b> {evidence_str}"
    )
    elements.append(Paragraph(meta_text, body_style))
    elements.append(Spacer(1, 12))

    # Executive Recommendation
    recommended_id = engine_result.get("recommended_route_id")
    ranked_routes = engine_result.get("ranked_routes", [])
    vulnerable_hub = engine_result.get("vulnerable_hub", "N/A")
    high_risk_edge = engine_result.get("high_risk_edge", "N/A")

    elements.append(Paragraph("1. Executive Route Recommendation", h2_style))

    if ranked_routes and recommended_id:
        best_route = ranked_routes[0]
        on_time_pct = int(round(best_route.get("on_time_probability", 0) * 100))
        rel_score = round(best_route.get("reliability_score", 0), 2)
        path_str = " &rarr; ".join(best_route.get("path", []))
        cum_time = best_route.get("cumulative_time", 0)

        justification = (
            f"<b>Recommendation: {recommended_id}</b> is selected as the optimal resilient path.<br/>"
            f"Under current evidence conditions, this route achieves an on-time arrival probability "
            f"of <b>{on_time_pct}%</b> with a composite reliability score of <b>{rel_score}</b> "
            f"(base travel time: <b>{cum_time:.0f} mins</b>).<br/>"
            f"<b>Path Sequence:</b> {path_str}<br/>"
            f"<i>Key Operational Advantage:</i> Successfully bypasses flagged chokepoint <b>{vulnerable_hub}</b> "
            f"and high-risk corridor edge <b>{high_risk_edge}</b>, minimizing stochastic cascading delay."
        )
        bg_color = colors.HexColor("#f0f9ff")
        border_color = colors.HexColor("#bae6fd")
    else:
        justification = (
            "<b>Warning:</b> No viable non-dominated route found satisfying the time budget under "
            "severe disruption. Consider increasing allowable time budget or deploying emergency rerouting."
        )
        bg_color = colors.HexColor("#fff1f2")
        border_color = colors.HexColor("#fecdd3")

    callout_data = [[Paragraph(justification, callout_style)]]
    callout_table = Table(callout_data, colWidths=[530])
    callout_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    elements.append(callout_table)
    elements.append(Spacer(1, 14))

    # Route Comparison Table
    elements.append(Paragraph("2. Non-Dominated Route Options (Chen et al. FSD Pruned)", h2_style))
    table_headers = [
        Paragraph("Route ID", table_cell_bold),
        Paragraph("Path", table_cell_bold),
        Paragraph("Travel Time", table_cell_bold),
        Paragraph("On-Time Prob", table_cell_bold),
        Paragraph("Reliability", table_cell_bold),
        Paragraph("Status", table_cell_bold),
    ]
    table_rows = [table_headers]

    for r in ranked_routes[:6]:
        r_id = r.get("route_id", "")
        p_list = r.get("path", [])
        p_short = " &rarr; ".join([p_list[0]] + p_list[1:-1] + [p_list[-1]]) if len(p_list) > 3 else " &rarr; ".join(p_list)
        time_val = f"{r.get('cumulative_time', 0):.0f} min"
        prob_val = f"{r.get('on_time_probability', 0)*100:.1f}%"
        rel_val = f"{r.get('reliability_score', 0):.3f}"
        status = "★ Recommended" if r_id == recommended_id else "Pareto Non-Dom."

        table_rows.append([
            Paragraph(r_id, table_cell_bold if r_id == recommended_id else table_cell),
            Paragraph(p_short, table_cell),
            Paragraph(time_val, table_cell),
            Paragraph(prob_val, table_cell),
            Paragraph(rel_val, table_cell),
            Paragraph(status, table_cell),
        ])

    if len(table_rows) > 1:
        route_table = Table(table_rows, colWidths=[60, 220, 65, 65, 55, 65])
        route_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ])
        )
        elements.append(route_table)
    else:
        elements.append(Paragraph("<i>No candidate routes available.</i>", body_style))

    elements.append(Spacer(1, 14))

    # Resilience Capabilities & Chokepoints
    elements.append(Paragraph("3. Network Resilience Scorecard & Chokepoint Diagnostics", h2_style))

    scorecard = engine_result.get("resilience_scorecard", {})
    r_resp = scorecard.get("rapid_response", 0.0)
    s_resist = scorecard.get("sustained_resistance", 0.0)
    c_run = scorecard.get("continuous_running", 0.0)
    r_conv = scorecard.get("rapid_convergence", 0.0)
    d_evol = scorecard.get("dynamic_evolution", 0.0)

    score_data = [
        [
            Paragraph("<b>Capability Metric</b>", table_cell_bold),
            Paragraph("<b>Score [0-1]</b>", table_cell_bold),
            Paragraph("<b>Operational Meaning</b>", table_cell_bold),
        ],
        [
            Paragraph("Rapid Response", table_cell),
            Paragraph(f"{r_resp:.2f}", table_cell_bold),
            Paragraph("Speed and sensitivity of belief updating upon sensor evidence", table_cell),
        ],
        [
            Paragraph("Sustained Resistance", table_cell),
            Paragraph(f"{s_resist:.2f}", table_cell_bold),
            Paragraph("System capacity to avoid high-delay states across operations", table_cell),
        ],
        [
            Paragraph("Continuous Running", table_cell),
            Paragraph(f"{c_run:.2f}", table_cell_bold),
            Paragraph("Stability and non-interruption of network flows", table_cell),
        ],
        [
            Paragraph("Rapid Convergence", table_cell),
            Paragraph(f"{r_conv:.2f}", table_cell_bold),
            Paragraph("Post-disruption recovery velocity back toward baseline", table_cell),
        ],
        [
            Paragraph("Dynamic Evolution", table_cell),
            Paragraph(f"{d_evol:.2f}", table_cell_bold),
            Paragraph("Longitudinal reliability trajectory across multi-period operations", table_cell),
        ],
    ]

    score_table = Table(score_data, colWidths=[130, 70, 330])
    score_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ])
    )
    elements.append(score_table)
    elements.append(Spacer(1, 10))

    # Diagnostics Box
    diag_text = (
        f"<b>Flagged Critical Vulnerabilities:</b><br/>"
        f"&bull; <b>Most Vulnerable Hub:</b> <font color='#b91c1c'><b>{vulnerable_hub}</b></font> "
        f"(highest degree-weighted disruption exposure).<br/>"
        f"&bull; <b>Highest Risk Edge:</b> <font color='#b91c1c'><b>{high_risk_edge}</b></font> "
        f"(bottleneck corridor edge vulnerable to combined weather/congestion delay)."
    )
    diag_table = Table([[Paragraph(diag_text, body_style)]], colWidths=[530])
    diag_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fecaca")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    elements.append(diag_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
