# PRD 4 — Technical Application Pipeline

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 3 (Pipeline)
**Feeds into:** PRD 5 (Model & Algorithm), PRD 6 (Inference Engine), PRD 7 (Frontend & UI)
**Status:** v1.0

---

## 1. Purpose

PRD 3 defined the conceptual pipeline (what algorithms run, in what order). This document defines how that pipeline becomes a running **application** — the three-layer system architecture, the concrete data contracts between layers, and the end-to-end sequence of events from a user action to a rendered result.

## 2. System architecture — three layers

```
+-----------------------------------------------------------+
|                 Resilient Route Advisor                    |
|                                                             |
|  +-------------------------------------------------------+ |
|  |  Model & Algorithm Layer            (PRD 5)            | |
|  |  networkx graph, pgmpy DBN, skew-t fitted CPTs,        | |
|  |  RSPP-LS / RSPP-A* pruning algorithm                   | |
|  +-------------------------------------------------------+ |
|                          |                                  |
|  +-------------------------------------------------------+ |
|  |  Inference Engine                    (PRD 6)           | |
|  |  Recomputes posteriors when evidence changes,          | |
|  |  outputs delay probability, reliability score          | |
|  +-------------------------------------------------------+ |
|                          |                                  |
|  +-------------------------------------------------------+ |
|  |  Streamlit Dashboard (Frontend/UI)   (PRD 7)           | |
|  |  Interactive network map, evidence toggles,            | |
|  |  route comparison table + resilience report,           | |
|  |  PDF export                                             | |
|  +-------------------------------------------------------+ |
+-----------------------------------------------------------+
```

This is a strict layered architecture: the Frontend never touches `pgmpy`/`networkx` directly — it only calls functions exposed by the Inference Engine, which in turn only calls functions exposed by the Model & Algorithm layer. This keeps each layer independently testable (PRD 5 can be unit-tested with no UI running at all).

## 3. Module boundaries and ownership

| Layer | Owns | Does NOT own |
|---|---|---|
| Model & Algorithm (PRD 5) | Graph construction, DBN structure/CPT definitions, skew-t fitting, pruning algorithm | Any notion of "current evidence" or UI state |
| Inference Engine (PRD 6) | Evidence injection, running inference, computing reliability/resilience scores, caching | Graph structure definition, rendering |
| Frontend/UI (PRD 7) | Widgets, visualization, session state, report export trigger | Any probability computation |

## 4. End-to-end sequence — "user toggles an evidence checkbox"

This is the single most important flow in the whole application; every demo moment in PRD 7 §5 is a variant of this sequence.

```
1. USER clicks "Heavy rain at Hub 4" checkbox in Streamlit UI.
2. FRONTEND callback fires -> calls
      inference_engine.update_evidence({"Hub4_Weather": "HeavyRain"})
3. INFERENCE ENGINE:
   a. Looks up current DBN time slice.
   b. Calls model_layer.run_inference(dbn, evidence) [pgmpy VariableElimination
      or BeliefPropagation].
   c. Receives posterior P(DelayState | evidence) for every hub/edge.
   d. Calls model_layer.rank_routes(graph, posteriors) -> RSPP-A* pruned list.
   e. Calls model_layer.compute_resilience(graph, posteriors) -> 5-capability
      scorecard + vulnerable hub/edge flag.
   f. Returns a single ENGINE_RESULT object (see data contract, sec 5) to
      the frontend.
4. FRONTEND:
   a. Recolors the network map nodes/edges based on ENGINE_RESULT.posteriors.
   b. Re-renders the route comparison table from ENGINE_RESULT.ranked_routes.
   c. Updates the resilience scorecard panel.
5. USER may now click "Export report" -> frontend calls
      inference_engine.generate_report(ENGINE_RESULT) -> PDF bytes -> download.
```

## 5. Data contract — `ENGINE_RESULT`

This is the single object passed from the Inference Engine to the Frontend after every evidence update. Defining it once here means PRD 6 and PRD 7 can be built in parallel against an agreed shape.

```python
ENGINE_RESULT = {
    "timestamp": "<ISO 8601 timestamp of this inference run>",
    "evidence_applied": {"Hub4_Weather": "HeavyRain"},
    "posteriors": {
        # one entry per node/edge in the graph
        "Hub4": {"Low": 0.10, "Medium": 0.35, "High": 0.55},
        "Hub4_Hub5_edge": {"Low": 0.15, "Medium": 0.40, "High": 0.45},
        # ...
    },
    "ranked_routes": [
        {
            "route_id": "R1",
            "path": ["Warehouse", "Hub1", "Hub7", "Hub13", "DeliveryZone"],
            "on_time_probability": 0.82,
            "reliability_score": 0.79,
            "dominated": False
        },
        # ...
    ],
    "resilience_scorecard": {
        "rapid_response": 0.71,
        "sustained_resistance": 0.66,
        "continuous_running": 0.58,
        "rapid_convergence": 0.63,
        "dynamic_evolution": 0.69
    },
    "vulnerable_hub": "Hub4",
    "high_risk_edge": "Hub4_Hub5_edge",
    "recommended_route_id": "R1"
}
```

## 6. Data contract — evidence input

```python
EVIDENCE_INPUT = {
    "<variable_name>": "<state_value>"
    # e.g. {"Hub4_Weather": "HeavyRain", "Hub9_Congestion": "High"}
}
```

Variable names must match exactly the node names defined in the Model & Algorithm layer's graph (PRD 5 §2). The Inference Engine validates this and raises a clear error rather than silently failing if the Frontend sends an unknown variable name.

## 7. Non-functional requirements

| Requirement | Target | Rationale |
|---|---|---|
| Inference latency after one evidence toggle | < 1.5 seconds | Must feel "live" during a class demo |
| Number of candidate routes considered before pruning | Up to ~40 for a 20-node grid | Matches the demo talking point "considered 40 candidate paths, pruned to 3" |
| Report export time | < 3 seconds | Keeps the demo flow uninterrupted |

## 8. Recommended build order (traceable to PRD 3 §4)

1. `networkx` graph + naive shortest path — sanity check, no BN yet.
2. Static `pgmpy` BN with discretized CPTs + evidence → posterior — Stage 4 working end-to-end.
3. Streamlit wrapper around step 2 — now interactive (minimum viable demo).
4. Add RSPP-A* pruning (Stage 6) instead of brute-force route comparison.
5. Add skew-t-fitted discretization (Stage 3) instead of placeholder CPT numbers.
6. Add the two-time-slice DBN layer (Stage 5) last — most technically involved, least essential if time runs short.

## 9. Acceptance criteria

- [ ] The three layers in §2 have no circular dependencies (Frontend → Inference Engine → Model layer, one direction only).
- [ ] `ENGINE_RESULT` (§5) is the only object the Frontend reads from the Inference Engine — no direct `pgmpy`/`networkx` imports in the Frontend code.
- [ ] The sequence in §4 can be demonstrated with a single evidence toggle producing a visibly updated result in under 1.5 seconds.
