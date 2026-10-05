# PRD 10 — Migrating the Original Idea to the Interactive Version

**Project:** Interactive Tamil Nadu Resilient Logistics Simulator
**Depends on:** PRD 1–7 (original academic pipeline), PRD 8–9 (new build)
**Status:** v1.0

---

## 1. Purpose

PRDs 1–7 defined a rigorous, paper-backed Bayesian/Dynamic Bayesian Network framework, demoed through a Streamlit dashboard on a 20-node grid. That framework is the actual coursework and must not be diluted. This document is the explicit mapping from the old plan to the new one, so nothing academically load-bearing gets lost while the presentation layer changes into something more ambitious.

## 2. What must be preserved unchanged

These are the pieces your grade depends on — none of them change with the new UI:

- The **combined problem statement** and the con-to-fix mapping (PRD 2) — path-centric correlated uncertainty, skew-t marginals, two-time-slice DBN, pruned α-reliable ranking.
- The **8-stage pipeline** (PRD 3) — network definition through final report. Every stage still exists; only Stage 1's node count and Stage 8's presentation change.
- The **RSPP-LS/RSPP-A* algorithm** (PRD 5 §7) — this is your hand-written algorithmic contribution and the strongest evidence of technical depth in a viva. It must still be visibly running and explainable, not hidden behind a slick UI.
- The **five resilience capabilities** (PRD 5 §8, from Jiang et al.) — still the basis of the resilience scorecard, whatever panel it's rendered in.
- The **paper citations and con-fix table** (PRD 1, PRD 2 §5) — when you present, the algorithmic contribution should still be traceable to specific limitations in specific papers, regardless of how good the map looks.

## 3. Mapping table — old element to new element

| Original (PRD 1–7) | New (PRD 8–9) | What changed and why |
|---|---|---|
| 20+ node abstract grid (1 warehouse, 18 hubs, 1 delivery zone) | 43-node Tamil Nadu hierarchy (3 HQ, 10 hubs, 30 warehouses) | Larger, geographically real, but same graph *role* — every node is still a warehouse/hub/delivery-zone-equivalent in the BN sense |
| Static evidence checkboxes ("Heavy rain at Hub 4") | Click-to-place hazard cell with intensity/radius sliders | Same *function* (injecting evidence) — the new UI is a richer front-end onto the same `hazard_exposure -> evidence` mechanism, not a different modeling approach |
| One evidence update -> one posterior snapshot | One hazard placement -> full multi-hour timeline of posteriors | This is the DBN (Stage 5) made visible as animation instead of a single "step forward" button — closer to what a two-time-slice DBN is actually for |
| Streamlit dashboard | React + Leaflet app | Presentation layer only — PRD 5 (Model & Algorithm) and PRD 6 (Inference Engine) are reused almost verbatim; only PRD 7 (Frontend) is replaced by PRD 9 |
| `ENGINE_RESULT` (single snapshot) | `ENGINE_TIMELINE_RESULT` (array of frames) | A superset of the original contract — the single-snapshot case is just `frames[-1]` |
| Manual "identify vulnerable hub" bullet | Cascade-effects panel, auto-derived from `resilience_metrics` | Same underlying computation (PRD 5 §8), now rendered as a cause-and-effect chain in the UI rather than a static text line |
| Corridor grouping for path-centric uncertainty (PRD 5 §4) | Same concept, re-scaled to the TN hierarchy | Adjacent hubs sharing a hazard's radius now play the role the original "same grid row" grouping played — the corridor concept doesn't change, only which nodes fall into which corridor |

## 4. What genuinely is new (not in the original scope)

Be upfront about this in your report — these are additions, not required by the course, and should be framed as "we extended the required scope to demonstrate the framework more concretely":

- Free-form hazard placement with continuous intensity/radius (vs. discrete evidence toggles).
- Full timeline animation and playback controls.
- A real geographic setting (Tamil Nadu) instead of an abstract grid.
- Shipment animation and any scoring/challenge features (if built).

## 5. Migration steps, in order

1. **Do not throw away the Streamlit prototype.** Keep it running against the 20-node grid as your fallback demo — if the React build isn't finished in time, you still have a working, correct BN demo to present.
2. **Re-run PRD 5's model layer against the new 43-node graph** before touching any UI code. If `graph_builder.py`, `dbn_model.py`, and `reliability_ranking.py` work correctly on 43 nodes (verified with the same kind of tests specified in PRD 5 §10), the hardest part is already validated.
3. **Introduce `hazard_exposure.py` (PRD 9 §4) as an additive module**, not a replacement — it sits in front of the existing `EVIDENCE_INPUT` contract (PRD 4 §6), translating hazard placements into the same evidence format the inference engine already accepts. The inference engine itself (PRD 6) does not need to change.
4. **Extend, don't rewrite, `ENGINE_RESULT`.** `ENGINE_TIMELINE_RESULT` (PRD 9 §6) wraps a list of the original per-frame shape — if time runs short, you can ship a version that only ever returns one frame and still be contract-compatible.
5. **Build the React frontend against the same acceptance criteria style as PRD 7** — no direct `pgmpy`/`networkx` imports in frontend code, exactly as before.
6. **Keep the RSPP-A* pruning count and resilience scorecard visible in the new UI**, even if reskinned — these are the two elements most likely to be asked about directly in a viva, since they're the parts a generic dashboard-generator (like the initial ChatGPT-drafted stack) wouldn't have included at all.

## 6. Risk: don't let the game overshadow the algorithm

The biggest risk in this migration is presentational — a slick, game-like map can make it *look* like the project is a visualization exercise rather than a probabilistic-reasoning one. Mitigate this explicitly:

- Always show the "pruned from N candidates" caption (PRD 7 §5.3) somewhere on screen, even in the new UI.
- Keep one moment in the demo where you pause the animation and explicitly narrate the inference happening — "the DBN just recomputed the posterior for every hub given this cyclone's exposure" — rather than letting the map speak for itself.
- In the written report, lead with PRD 2's problem statement and PRD 1's citations before showing screenshots of the interactive map, not after.

## 7. Acceptance criteria

- [ ] Every item in §2 ("what must be preserved") is identifiable and explainable in the final build, not just present in the codebase.
- [ ] The Streamlit prototype (PRD 7) still runs as a fallback and is not deleted from the repository.
- [ ] `hazard_exposure.py` is additive to, not a replacement for, the existing `EVIDENCE_INPUT`/inference engine contract.
- [ ] The report explicitly separates "required framework" (PRD 1–7) from "extended demonstration" (PRD 8–10) so graders can assess the core contribution independently of the presentation layer.
