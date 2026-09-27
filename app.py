"""
app.py — Resilient Route Advisor (PRD 7: Streamlit Application Entry Point)

Interactive Decision Support System for Logistics Networks under Uncertainty.
Complies strictly with PRD 7 §9:
  - ZERO imports of networkx or pgmpy.
  - Interacts exclusively with inference_engine's public API.
"""

from __future__ import annotations
import streamlit as st

from inference_engine import (
    EngineState,
    update_evidence,
    initialize_engine,
    generate_report,
)
from components.evidence_panel import render_evidence_panel
from components.network_map import render_network_map
from components.route_table import render_route_table
from components.resilience_panel import render_resilience_panel


# ---------------------------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Resilient Route Advisor",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished dashboard look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #e0f2fe;
        color: #0369a1;
        margin-right: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session State Initialization (Built ONCE per session per PRD 7 §7)
# ---------------------------------------------------------------------------
if "initialized" not in st.session_state:
    with st.spinner("Initializing Bayesian Logistics Model & Dynamic Corridors..."):
        G, bn, state, initial_result = initialize_engine(
            include_temporal=True,
            time_budget=200.0,
        )
        st.session_state.G = G
        st.session_state.bn = bn
        st.session_state.engine_state = state
        st.session_state.last_result = initial_result
        st.session_state.time_budget = 200.0
        st.session_state.initialized = True


# ---------------------------------------------------------------------------
# Event Handlers
# ---------------------------------------------------------------------------
def handle_evidence_update(evidence: dict[str, str], time_budget: float) -> None:
    """Callback triggered when user applies new evidence or changes budget."""
    st.session_state.time_budget = time_budget
    result = update_evidence(
        state=st.session_state.engine_state,
        bn=st.session_state.bn,
        G=st.session_state.G,
        new_evidence=evidence,
        time_budget=time_budget,
    )
    st.session_state.last_result = result


def handle_step_forward() -> None:
    """Callback to advance DBN time slice without fresh evidence."""
    st.session_state.engine_state.step_forward()
    # Query belief evolution under temporal persistence
    result = update_evidence(
        state=st.session_state.engine_state,
        bn=st.session_state.bn,
        G=st.session_state.G,
        new_evidence={},
        time_budget=st.session_state.time_budget,
    )
    st.session_state.last_result = result


def handle_reset() -> None:
    """Callback to reset engine to clean baseline state."""
    st.session_state.engine_state.reset()
    result = update_evidence(
        state=st.session_state.engine_state,
        bn=st.session_state.bn,
        G=st.session_state.G,
        new_evidence={},
        time_budget=200.0,
    )
    st.session_state.last_result = result
    st.session_state.time_budget = 200.0


# ---------------------------------------------------------------------------
# Main Layout
# ---------------------------------------------------------------------------
current_result = st.session_state.last_result
time_slice = current_result.get("time_slice", 0)

# Top Bar Header
header_col, action_col = st.columns([3, 1])

with header_col:
    st.markdown('<div class="main-header">🚚 Resilient Route Advisor</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">'
        f'<span class="badge">Temporal Horizon: t = {time_slice} hrs</span>'
        f'Dynamic Bayesian Network Decision Support & Stochastic Route Reliability'
        f'</div>',
        unsafe_allow_html=True,
    )

with action_col:
    ranked_routes = current_result.get("ranked_routes", [])
    if ranked_routes:
        pdf_bytes = generate_report(current_result)
        st.download_button(
            label="📄 Export Report PDF",
            data=pdf_bytes,
            file_name=f"logistics_resilience_report_t{time_slice}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            help="Download the formal executive Probabilistic Logistics Resilience Report.",
        )
    else:
        st.button("📄 Export Report PDF", disabled=True, use_container_width=True)

# Sidebar: Evidence Panel
with st.sidebar:
    render_evidence_panel(
        on_evidence_change=handle_evidence_update,
        on_step_forward=handle_step_forward,
        on_reset=handle_reset,
        current_time_slice=time_slice,
        current_evidence=current_result.get("evidence_applied", {}),
    )

# Right Main Area: Map + Route Table + Resilience Scorecard
render_network_map(current_result)

st.markdown("---")

render_route_table(current_result)

st.markdown("---")

render_resilience_panel(current_result)
