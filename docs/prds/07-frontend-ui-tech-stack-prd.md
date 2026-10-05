# PRD 7 — Frontend + User Interface (Tech Stack + Logic)

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 4 (Technical Application Pipeline), PRD 6 (Inference Engine)
**Status:** v1.0

---

## 1. Purpose

This is the only layer the audience actually sees during the demo. It defines the tech stack, the exact widgets on screen, the wireframe layout, and the event-handling logic that connects user actions to `inference_engine.update_evidence()` calls (PRD 6 §5).

## 2. Tech stack for this layer

| Component | Library | Purpose |
|---|---|---|
| App framework | `Streamlit` | Rapid interactive dashboard, no separate frontend build step |
| Network visualization | `pyvis` (physics-based interactive graph) or `plotly.graph_objects` (network trace) | Renders the 20-node grid with color-coded delay states |
| Tabular display | Streamlit native `st.dataframe` / `st.table` | Route comparison table |
| Session state | `st.session_state` | Holds the `EngineState` object and `dbn`/`G` objects across reruns |
| File download | `st.download_button` | Serves the PDF report from `report_generator.generate_report()` |

## 3. Application name and framing

**"Resilient Route Advisor"** — single-page Streamlit app, three visible panels plus a header.

## 4. Wireframe (textual layout)

```
+---------------------------------------------------------------+
| Resilient Route Advisor                    [Export report PDF] |
+---------------------------------------------------------------+
| EVIDENCE PANEL (left, ~25% width)   | NETWORK MAP (right, ~75%) |
|--------------------------------------|                          |
| [ ] Heavy rain at Hub 4              |   (pyvis/plotly           |
| [ ] Heavy rain at Hub 11             |    interactive graph,     |
| [ ] High congestion at Hub 8         |    nodes colored by       |
| [ ] Demand surge at Delivery Zone    |    current delay state:   |
| Time slice: [ Step forward -> ]      |    green/amber/red)       |
|                                       |                          |
+---------------------------------------------------------------+
| ROUTE COMPARISON TABLE (full width)                             |
|  Route | Path            | On-time % | Reliability | Recommended|
|  R1    | WH-H1-H7-H13-DZ | 82%       | 0.79        |     *      |
|  R2    | WH-H4-H5-H11-DZ | 41%       | 0.38        |            |
+---------------------------------------------------------------+
| RESILIENCE SCORECARD (full width)                               |
|  Rapid response: 0.71   Sustained resistance: 0.66              |
|  Continuous running: 0.58   Rapid convergence: 0.63              |
|  Dynamic evolution: 0.69                                         |
|  Vulnerable hub: Hub4      High-risk edge: Hub4-Hub5             |
+---------------------------------------------------------------+
```

## 5. Component breakdown

### 5.1 Evidence panel (`components/evidence_panel.py`)
- One checkbox/select box per evidence variable defined in the DBN (must match names in `dbn.nodes()` exactly — validated by PRD 6 §4's `validate_evidence`).
- A "Step forward in time" button that advances `EngineState.current_time_slice` without necessarily adding new evidence — this is what demonstrates Pipeline Stage 5 (DBN belief evolving/decaying even without new input).

### 5.2 Network map (`components/network_map.py`)
- Built from the same `networkx` graph object used by the Model layer (PRD 5 §3) — never a separately hand-drawn diagram, so the map always reflects the actual graph structure.
- Node fill color mapped from `ENGINE_RESULT.posteriors[node]["High"]` probability: green (< 0.33), amber (0.33–0.66), red (> 0.66).
- The recommended route's edges are drawn with a distinct highlight (e.g., thicker green stroke) using `ENGINE_RESULT.recommended_route_id`.

### 5.3 Route comparison table (`components/route_table.py`)
- Rendered directly from `ENGINE_RESULT.ranked_routes` — no client-side recomputation.
- Highlights the recommended route row.
- Shows a "pruned from N candidates" caption using the count of routes considered before dominance pruning (PRD 5 §7), to make the RSPP-A* contribution visible rather than implicit.

### 5.4 Resilience scorecard (`components/resilience_panel.py`)
- Renders the five capabilities from `ENGINE_RESULT.resilience_scorecard` as simple metric widgets (`st.metric`).
- Displays `vulnerable_hub` and `high_risk_edge` as flagged text, matching the baseline PPT's "Identify Network Vulnerabilities" step.

### 5.5 Export button (header)
- Calls `inference_engine.generate_report(ENGINE_RESULT)`.
- Disabled (grayed out) whenever `ENGINE_RESULT.ranked_routes` is empty (per PRD 6 §8's error-handling requirement).

## 6. Event-handling logic (main app loop)

```python
import streamlit as st
from inference_engine import EngineState, update_evidence, generate_report
from model_layer import graph_builder, dbn_model

st.set_page_config(page_title="Resilient Route Advisor", layout="wide")

if "engine_state" not in st.session_state:
    st.session_state.engine_state = EngineState()
    st.session_state.G = graph_builder.build_logistics_graph()
    st.session_state.dbn = dbn_model.build_dbn(...)   # built once, cached

st.title("Resilient Route Advisor")

with st.sidebar:
    st.subheader("Evidence")
    evidence = {}
    if st.checkbox("Heavy rain at Hub 4"):
        evidence["Hub4_Weather"] = "HeavyRain"
    if st.checkbox("High congestion at Hub 8"):
        evidence["Hub8_Congestion"] = "High"
    # ... remaining evidence toggles
    step_forward = st.button("Step forward in time")

if evidence or step_forward:
    result = update_evidence(
        st.session_state.engine_state,
        st.session_state.dbn,
        st.session_state.G,
        evidence,
    )
    st.session_state.last_result = result

if "last_result" in st.session_state:
    render_network_map(st.session_state.G, st.session_state.last_result)
    render_route_table(st.session_state.last_result)
    render_resilience_panel(st.session_state.last_result)

    if st.session_state.last_result["ranked_routes"]:
        pdf_bytes = generate_report(st.session_state.last_result)
        st.download_button("Export report PDF", data=pdf_bytes,
                            file_name="resilience_report.pdf")
    else:
        st.warning("No reliable route found under current evidence.")
```

## 7. Session state rules

- The `networkx` graph and `pgmpy` DBN objects are built **once** per session (on first load) and stored in `st.session_state` — never rebuilt on every widget interaction, since that would defeat the < 1.5s latency target from PRD 4 §7.
- `EngineState` (evidence + time slice + history) persists in `st.session_state` for the life of the browser session; a "Reset demo" button (optional, recommended for live demos) clears it back to a fresh `EngineState()`.

## 8. Demo script mapped to UI actions (for the live presentation)

| Demo moment | UI action | What the audience sees |
|---|---|---|
| 1. Baseline | Load app, no evidence checked | Naive shortest route highlighted, all nodes green |
| 2. Live evidence injection | Check "Heavy rain at Hub 4" | Network map recolors around Hub 4, route table re-ranks in real time |
| 3. Time-lapse | Click "Step forward in time" a few times | Posteriors visibly evolve without new evidence — the DBN, not a one-shot BN |
| 4. Reliability ranking proof | Point at the "pruned from N candidates" caption | Makes the RSPP-A* pruning algorithm visible, not just claimed |
| 5. Report export | Click "Export report PDF" | Generated Probabilistic Logistics Resilience Report downloads live |

## 9. Acceptance criteria

- [ ] No `pgmpy` or `networkx` import appears anywhere in `components/*.py` or the main app file — only calls into `inference_engine`'s three public functions (PRD 6 §9).
- [ ] Every evidence checkbox label maps to exactly one valid DBN node name (verified against PRD 6 §4's validator, not just assumed).
- [ ] The app never crashes on zero-route results — §5.5 and §6's warning branch are both implemented and tested.
- [ ] The wireframe in §4 is realized in the actual running app before the demo date.
