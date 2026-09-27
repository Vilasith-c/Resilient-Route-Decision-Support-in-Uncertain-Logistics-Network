"""
evidence_panel.py — Component 1: Evidence Injection & Scenario Controls (PRD 7 §5.1)

Provides UI controls for evidence injection, scenario presets, time-stepping,
and search parameters without importing pgmpy or networkx.
"""

from __future__ import annotations
import streamlit as st
from typing import Callable, Any


def render_evidence_panel(
    on_evidence_change: Callable[[dict[str, str], float], None],
    on_step_forward: Callable[[], None],
    on_reset: Callable[[], None],
    current_time_slice: int = 0,
    current_evidence: dict[str, str] | None = None,
) -> None:
    """
    Render the evidence sidebar panel.

    Parameters
    ----------
    on_evidence_change : callable
        Callback receiving (evidence_dict, time_budget).
    on_step_forward : callable
        Callback to advance DBN time slice.
    on_reset : callable
        Callback to reset session.
    current_time_slice : int
        Current active time slice.
    current_evidence : dict or None
        Active evidence in state.
    """
    st.subheader("⚡ Disruption Scenarios")

    preset = st.selectbox(
        "Load Preset Demo Scenario",
        [
            "Custom Controls",
            "Scenario A: Clear Baseline (Normal Ops)",
            "Scenario B: Northern Storm (Hub 4 Heavy Rain)",
            "Scenario C: Central Corridor Bottleneck (Hub 5 & 8 Congestion)",
            "Scenario D: Compound Crisis (Hub 4 Storm + Hub 8 Congestion + Hub 11 Storm)",
        ],
        index=0,
        help="Quickly load pre-configured disruption scenarios matching the demo presentation.",
    )

    st.markdown("---")
    st.subheader("🌧️ Weather Evidence")

    weather_evidence = {}
    hub4_rain = st.checkbox(
        "Hub 4 — Heavy Rain",
        value=(preset in ["Scenario B: Northern Storm (Hub 4 Heavy Rain)", "Scenario D: Compound Crisis (Hub 4 Storm + Hub 8 Congestion + Hub 11 Storm)"]),
        help="Left-tier regional sorting hub weather exposure.",
    )
    if hub4_rain:
        weather_evidence["Hub4_Weather"] = "HeavyRain"

    hub11_rain = st.checkbox(
        "Hub 11 — Heavy Rain",
        value=(preset == "Scenario D: Compound Crisis (Hub 4 Storm + Hub 8 Congestion + Hub 11 Storm)"),
        help="South-central regional hub severe weather.",
    )
    if hub11_rain:
        weather_evidence["Hub11_Weather"] = "HeavyRain"

    hub1_rain = st.checkbox(
        "Hub 1 — Light Rain",
        value=False,
        help="North-west entry hub precipitation.",
    )
    if hub1_rain:
        weather_evidence["Hub1_Weather"] = "LightRain"

    st.markdown("---")
    st.subheader("🚚 Congestion Evidence")

    congestion_evidence = {}
    hub8_cong = st.checkbox(
        "Hub 8 — High Congestion",
        value=(preset in ["Scenario C: Central Corridor Bottleneck (Hub 5 & 8 Congestion)", "Scenario D: Compound Crisis (Hub 4 Storm + Hub 8 Congestion + Hub 11 Storm)"]),
        help="Critical central chokepoint facility volume overflow.",
    )
    if hub8_cong:
        congestion_evidence["Hub8_Congestion"] = "High"

    hub5_cong = st.checkbox(
        "Hub 5 — High Congestion",
        value=(preset == "Scenario C: Central Corridor Bottleneck (Hub 5 & 8 Congestion)"),
        help="Mid-column bottleneck facility sorting delay.",
    )
    if hub5_cong:
        congestion_evidence["Hub5_Congestion"] = "High"

    hub14_cong = st.checkbox(
        "Hub 14 — High Congestion",
        value=False,
        help="Southern tier regional hub bottleneck.",
    )
    if hub14_cong:
        congestion_evidence["Hub14_Congestion"] = "High"

    st.markdown("---")
    st.subheader("⏱️ Route Parameters")
    time_budget = st.slider(
        "Delivery Time Budget (mins)",
        min_value=120,
        max_value=280,
        value=200,
        step=10,
        help="Upper bound travel time allowed for non-dominated route exploration (Chen et al. 2012).",
    )

    combined_evidence = {**weather_evidence, **congestion_evidence}

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Apply Evidence", type="primary", use_container_width=True):
            on_evidence_change(combined_evidence, float(time_budget))
    with col2:
        if st.button("Reset Demo", use_container_width=True):
            on_reset()

    st.markdown("---")
    st.subheader(f"⏳ Temporal DBN (t = {current_time_slice})")
    st.caption("Advance time slice to observe belief decay and temporal persistence without new inputs (Jiang et al. 2023).")
    if st.button("⏩ Step Forward in Time", use_container_width=True):
        on_step_forward()
