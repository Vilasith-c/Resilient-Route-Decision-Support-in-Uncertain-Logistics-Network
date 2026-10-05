# PRD 6 — Inference Engine (Tech Stack)

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 4 (Technical Application Pipeline), PRD 5 (Model & Algorithm)
**Consumed by:** PRD 7 (Frontend & UI)
**Status:** v1.0

---

## 1. Purpose

The Inference Engine is the middle layer: it owns "the current state of the world" (what evidence has been applied, what time slice we're on) and orchestrates calls into the Model & Algorithm layer (PRD 5) to produce the single `ENGINE_RESULT` object the Frontend (PRD 7) renders. Nothing in this layer draws a pixel; nothing in this layer defines graph structure from scratch.

## 2. Tech stack for this layer

| Component | Library | Purpose |
|---|---|---|
| Inference algorithm | `pgmpy.inference.VariableElimination` (or `BeliefPropagation` for larger networks) | Runs exact inference over the DBN given evidence |
| State/session management | Plain Python object (a small `EngineState` class) or `functools.lru_cache` for memoizing repeated evidence combinations | Avoids recomputing identical evidence sets during a demo |
| Report rendering | `reportlab` or `weasyprint` (HTML → PDF) | Turns `ENGINE_RESULT` into the exportable PDF |
| Serialization | `dataclasses` + `json` | Defines and validates the `ENGINE_RESULT`/`EVIDENCE_INPUT` contracts from PRD 4 §5–6 |

## 3. Module: `engine_state.py`

**Responsibility:** Track the current evidence set and current DBN time slice across the demo session.

```python
from dataclasses import dataclass, field

@dataclass
class EngineState:
    current_time_slice: int = 0
    applied_evidence: dict = field(default_factory=dict)
    history: list = field(default_factory=list)   # list of past ENGINE_RESULT snapshots

    def apply_evidence(self, new_evidence: dict):
        """
        Merges new_evidence into applied_evidence and advances
        current_time_slice by 1 (Pipeline Stage 5 -- DBN temporal step).
        """
        self.applied_evidence.update(new_evidence)
        self.current_time_slice += 1
```

## 4. Module: `inference_runner.py` (Pipeline Stage 4 & 5)

**Responsibility:** Wraps `pgmpy` inference calls; this is the only module allowed to import `pgmpy.inference`.

```python
from pgmpy.inference import VariableElimination

def run_inference(dbn, evidence: dict, time_slice: int) -> dict:
    """
    Runs exact inference over the DBN unrolled to `time_slice`.
    evidence keys must be validated against dbn node names before this
    is called (see validate_evidence below) -- an unknown variable name
    raises ValueError rather than failing silently inside pgmpy.

    Returns: {node_name: {"Low": p, "Medium": p, "High": p}, ...}
    """
    infer = VariableElimination(dbn)
    result = {}
    for node in dbn.nodes():
        if node[1] != time_slice:
            continue
        query = infer.query(variables=[node], evidence=evidence, show_progress=False)
        result[node[0]] = dict(zip(query.state_names[node], query.values))
    return result

def validate_evidence(dbn, evidence: dict) -> None:
    """Raises ValueError listing any evidence key not present in dbn.nodes()."""
    valid_names = {n[0] for n in dbn.nodes()}
    unknown = set(evidence.keys()) - valid_names
    if unknown:
        raise ValueError(f"Unknown evidence variable(s): {unknown}")
```

## 5. Module: `engine.py` — the orchestration entry point

**Responsibility:** The single public function the Frontend calls. Implements the sequence defined in PRD 4 §4.

```python
from datetime import datetime, timezone
from model_layer import reliability_ranking, resilience_metrics

def update_evidence(state: "EngineState", dbn, G, new_evidence: dict) -> dict:
    """
    Full pipeline Stage 4-8 orchestration for one evidence update.
    Returns an ENGINE_RESULT dict per the PRD 4 SS5 data contract.
    """
    validate_evidence(dbn, new_evidence)
    state.apply_evidence(new_evidence)

    posteriors = run_inference(dbn, state.applied_evidence, state.current_time_slice)

    ranked = reliability_ranking.rspp_astar(
        G, source="Warehouse", target="DeliveryZone",
        time_budget=..., heuristic=...
    )
    scorecard = resilience_metrics.compute_resilience_scorecard(state.history + [posteriors])
    vulnerable_hub = resilience_metrics.identify_vulnerable_hub(G, posteriors)
    high_risk_edge = resilience_metrics.identify_high_risk_edge(G, posteriors)

    engine_result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence_applied": dict(state.applied_evidence),
        "posteriors": posteriors,
        "ranked_routes": [label_to_dict(l) for l in ranked],
        "resilience_scorecard": scorecard,
        "vulnerable_hub": vulnerable_hub,
        "high_risk_edge": high_risk_edge,
        "recommended_route_id": ranked[0].route_id if ranked else None,
    }
    state.history.append(engine_result)
    return engine_result
```

## 6. Module: `report_generator.py` (Pipeline Stage 8)

**Responsibility:** Render `ENGINE_RESULT` into the downloadable Probabilistic Logistics Resilience Report.

```python
def generate_report(engine_result: dict) -> bytes:
    """
    Builds a PDF containing:
      - Route comparison table (delay probability / on-time probability /
        reliability rating per route)
      - Flagged vulnerable hub and high-risk edge
      - Recommended route with plain-language justification, e.g.:
        "Route R1 is recommended: 82% on-time probability under current
         evidence, avoiding the high-risk Hub4-Hub5 corridor."
    Returns raw PDF bytes for Streamlit's download_button.
    """
    ...
```

## 7. Caching / performance strategy

- Memoize `run_inference` results keyed on `(frozenset(evidence.items()), time_slice)` — repeated toggles of the same checkbox during a demo should not recompute inference.
- Cap `rspp_astar` candidate generation at a configurable ceiling (e.g., 40 candidate paths) to guarantee the < 1.5s latency target from PRD 4 §7.
- The DBN is unrolled only to `current_time_slice + 1` at any point — never pre-unrolled to an arbitrary horizon, to keep inference cost bounded.

## 8. Error handling requirements

| Failure case | Required behavior |
|---|---|
| Frontend sends an evidence variable name not in the DBN | Raise `ValueError` with the offending name(s); Frontend must catch and show an inline error, never crash the app |
| `rspp_astar` finds zero non-dominated routes reaching the delivery zone | Return an empty `ranked_routes` list and set `recommended_route_id: None`; Frontend must render "no reliable route found under current evidence" rather than a blank table |
| Report generation fails | Return `None`; Frontend disables the download button and shows a retry option |

## 9. Public API summary (what PRD 7 is allowed to call)

```python
from inference_engine import EngineState, update_evidence, generate_report

state = EngineState()
result = update_evidence(state, dbn, G, {"Hub4_Weather": "HeavyRain"})
pdf_bytes = generate_report(result)
```

This three-function surface is the **entire** contract the Frontend depends on — no other inference-layer function should be imported from `inference_engine` by PRD 7 code.

## 10. Acceptance criteria

- [ ] `update_evidence` returns an object exactly matching the `ENGINE_RESULT` schema in PRD 4 §5.
- [ ] Unknown evidence variables raise a catchable, descriptive error rather than a `pgmpy` internal exception.
- [ ] Repeated calls with identical evidence do not re-run `pgmpy` inference (cache hit verified in a test).
- [ ] End-to-end latency from `update_evidence` call to return is under 1.5 seconds on the 20-node graph.
