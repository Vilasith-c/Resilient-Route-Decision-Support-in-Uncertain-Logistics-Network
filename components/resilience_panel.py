"""
resilience_panel.py — Component 4: Resilience Scorecard & Chokepoints (PRD 7 §5.4)

Renders the five DBN resilience capabilities from Jiang et al. (2023)
along with identified critical network vulnerabilities.
ZERO imports of networkx or pgmpy.
"""

from __future__ import annotations
from typing import Any
import streamlit as st


def render_resilience_panel(engine_result: dict[str, Any]) -> None:
    """
    Render the resilience scorecard panel and vulnerability diagnostics.

    Parameters
    ----------
    engine_result : dict
        ENGINE_RESULT dictionary containing resilience_scorecard,
        vulnerable_hub, and high_risk_edge.
    """
    st.subheader("🛡️ Dynamic Network Resilience Scorecard (Jiang et al. 2023)")

    scorecard = engine_result.get("resilience_scorecard", {})
    vulnerable_hub = engine_result.get("vulnerable_hub", "N/A")
    high_risk_edge = engine_result.get("high_risk_edge", "N/A")

    # 5 Metric columns
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            label="⚡ Rapid Response",
            value=f"{scorecard.get('rapid_response', 0.5):.2f}",
            help="Sensitivity and agility of posterior updating when new sensor evidence is registered.",
        )
    with c2:
        st.metric(
            label="🛡️ Sustained Resistance",
            value=f"{scorecard.get('sustained_resistance', 0.5):.2f}",
            help="Network capacity to prevent delay degradation under sustained disruption.",
        )
    with c3:
        st.metric(
            label="🔄 Continuous Running",
            value=f"{scorecard.get('continuous_running', 0.5):.2f}",
            help="Stability and non-interruption of non-dominated logistical delivery flows.",
        )
    with c4:
        st.metric(
            label="📈 Rapid Convergence",
            value=f"{scorecard.get('rapid_convergence', 0.5):.2f}",
            help="Post-disruption recovery speed returning toward nominal baseline operations.",
        )
    with c5:
        st.metric(
            label="🌱 Dynamic Evolution",
            value=f"{scorecard.get('dynamic_evolution', 0.5):.2f}",
            help="Trajectory of overall network reliability across multi-period operations.",
        )

    # Vulnerability alerts
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.error(
            f"🎯 **Most Vulnerable Hub:** `{vulnerable_hub}`  \n"
            f"High degree centrality combined with cascading delay potential."
        )
    with col_v2:
        st.warning(
            f"⚠️ **Highest-Risk Edge Corridor:** `{high_risk_edge}`  \n"
            f"Corridor bottleneck with severe disruption and weather vulnerability."
        )
