# PRD 9 — Tech Stack + Plan + Pipeline (UI + Backend)

**Project:** Interactive Tamil Nadu Resilient Logistics Simulator
**Depends on:** PRD 8 (Readiness), PRD 5/6 (Model & Inference Engine — reused, not replaced)
**Status:** v1.0

---

## 1. Purpose

This document is the concrete build spec for the interactive, click-to-place, game-like version of the application: final tech stack, three-layer architecture, the exact click → intensity → evidence → animation pipeline, and the data contracts a frontend and backend developer can build against in parallel.

## 2. Final tech stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend framework | React + TypeScript + Vite | Replaces the Streamlit plan from PRD 7 |
| Styling | Tailwind CSS | Light, minimal, professional per the agreed visual direction |
| Map | `react-leaflet`, canvas renderer | 43 nodes + ~40 routes is well within Leaflet's comfort zone |
| Basemap tiles | CARTO Positron (light) or equivalent | Confirm current usage terms before any public deployment |
| Icons | Lucide React | Matches the mockup's icon style |
| Charts | Recharts | Impact panel, timeline graphs |
| Backend framework | FastAPI (Python) | Thin wrapper around the existing model/inference layers |
| Graph | `networkx` | 43-node graph, unchanged in kind from PRD 5, smaller in size |
| Bayesian/Dynamic BN | `pgmpy` | Reused from PRD 5/6; fallback below if latency testing fails |
| Fallback inference | Hand-written numpy forward-filter | Only if PRD 8 §6's latency test shows `pgmpy` too slow for interactive use |
| Distributions | `scipy.stats` (skewnorm/nct) | Unchanged from PRD 5 §5 |
| Routing geometry | OpenRouteService or OSRM, precomputed once | Cached to a local GeoJSON file, not queried live per interaction |
| Data storage | Flat JSON/GeoJSON files | No database needed at 43 nodes |
| Real-time channel | None — polling/local animation instead | See §4; WebSockets are unnecessary overhead at this scale |

## 3. System architecture

```
+--------------------------------------------------------------+
|                     React + TypeScript App                    |
|                                                                |
|  Map (react-leaflet)      Hazard placement UI    Timeline/    |
|  - node markers           - click to place cell  playback     |
|  - route lines            - intensity/radius      controls    |
|  - color by exposure        sliders                            |
+---------------------------------|------------------------------+
                                  | REST (fetch/axios)
                                  v
+--------------------------------------------------------------+
|                          FastAPI Backend                       |
|  POST /hazard         -> apply a hazard cell, return timeline  |
|  GET  /network        -> node/edge structure (loaded once)     |
|  POST /hazard/clear   -> remove a hazard cell                  |
+---------------------------------|------------------------------+
                                  v
+--------------------------------------------------------------+
|              Model & Inference Layer (PRD 5 / PRD 6)          |
|  networkx graph (43 nodes)  |  pgmpy DBN  |  reliability_ranking|
|  hazard exposure calculator |  resilience_metrics               |
+--------------------------------------------------------------+
```

This preserves PRD 5 and PRD 6 almost unchanged — the only new module is the **hazard exposure calculator**, described below.

## 4. New module: `hazard_exposure.py`

**Responsibility:** Convert a placed hazard cell (type, location, intensity, radius) into evidence the DBN can consume.

```python
def compute_exposure(node_or_edge_location, hazard) -> float:
    """
    hazard = {"type": "flood", "lat": ..., "lon": ..., "intensity": 0.6, "radius_km": 40}
    Returns exposure in [0, 1] = hazard["intensity"] * falloff(distance, radius_km)
    falloff is 1.0 at the center, decaying to 0 at the edge of radius_km
    (linear or gaussian falloff -- linear is simplest and defensible for a demo)
    """
    ...

def exposure_to_evidence_state(exposure: float, hazard_type: str) -> str:
    """
    Maps a continuous exposure value to a discrete CPT state (Low/Medium/High)
    using the hazard-effect mapping table from PRD 8 SS3.
    """
    ...
```

This is the piece that makes "60% rain" meaningful: it is not a raw probability fed directly into the BN, it is an *exposure* that then gets discretized per the hazard-effect mapping table your team defines in PRD 8.

## 5. Data contract — hazard placement request

```python
HAZARD_INPUT = {
    "hazard_id": "h1",
    "type": "flood" | "cyclone" | "heatwave" | "landslide" | "road_closure" | "hub_outage",
    "lat": 13.0827,
    "lon": 80.2707,
    "intensity": 0.6,      # 0.0-1.0, shown to user as 0-100%
    "radius_km": 40,
    "start_time": 0        # simulation hour at which this hazard begins
}
```

## 6. Data contract — engine response (time-indexed)

Unlike PRD 4's single-snapshot `ENGINE_RESULT`, the interactive/game version returns the **entire timeline in one response**, so the frontend can scrub/play it locally without re-querying the backend on every timestep.

```python
ENGINE_TIMELINE_RESULT = {
    "hazard_applied": HAZARD_INPUT,
    "frames": [
        {
            "time_hour": 0,
            "node_states": {"HQ_Chennai": "Low", "Hub_Sriperumbudur": "High", ...},
            "route_status": [
                {"route_id": "R1", "operational_pct": 0.82, "path": [...]},
                ...
            ],
            "cascade_effects": [
                {"node": "Hub_Sriperumbudur", "impact": "High"},
                {"node": "Warehouse_12", "impact": "Delay likely"}
            ]
        },
        # one entry per simulated hour, e.g. 0..10
    ],
    "resilience_scorecard": { ... },        # from PRD 5 SS8, computed at final frame
    "vulnerable_hub": "Hub_Sriperumbudur",
    "high_risk_edge": "HQ_Chennai__Hub_Sriperumbudur"
}
```

## 7. End-to-end pipeline — "user places a hazard cell"

```
1. USER clicks a hazard icon, then clicks a point on the Tamil Nadu map.
2. FRONTEND opens the intensity/radius popup (matches the mockup's event
   config popup); user adjusts sliders.
3. USER confirms -> FRONTEND POSTs HAZARD_INPUT to /hazard.
4. BACKEND:
   a. hazard_exposure.compute_exposure() for every node/edge within radius.
   b. exposure_to_evidence_state() -> discrete evidence per affected node.
   c. For each simulated hour (0..10):
        - advance the DBN one time slice (PRD 5 dbn_model, PRD 6 inference_runner)
        - run reliability_ranking.rspp_astar() for current posteriors
        - run resilience_metrics for the running scorecard
        - append a frame to ENGINE_TIMELINE_RESULT.frames
   d. Return the full ENGINE_TIMELINE_RESULT.
5. FRONTEND:
   a. Stores the full timeline in local state.
   b. Timeline slider/play button scrubs through `frames` locally --
      no further backend calls needed until a new hazard is placed.
   c. Map recolors nodes/edges per the current frame; shipment markers
      (optional, later milestone) animate along route paths.
```

## 8. Latency and debounce strategy

- Sliders (intensity, radius) update a **local preview** only (client-side approximate recoloring) while dragging.
- The actual `/hazard` POST fires only on slider release (debounced), per PRD 8 §4's decision.
- If PRD 8 §6's latency test shows `pgmpy` inference per frame is too slow for a 10-frame timeline to return in a reasonable time (target: under ~2 seconds total for the whole timeline), fall back to the numpy forward-filter for the temporal loop, keeping `pgmpy` only for the static per-frame BN query.

## 9. Build order

1. Finalize the 43-node graph and hazard-effect mapping table (PRD 8 deliverables).
2. Build `hazard_exposure.py` and test it against the static BN from PRD 5/6 with one hazard, one frame (no timeline yet).
3. Wrap in FastAPI (`/network`, `/hazard`) returning a single-frame result.
4. Build the React map + hazard placement popup against that single-frame endpoint.
5. Extend the backend to return the full `frames` timeline; add the DBN temporal loop.
6. Add the timeline scrub/play control on the frontend.
7. Add the resilience scorecard and cascade-effects panel.
8. Optional: shipment animation along routes, scoring/challenges.

## 10. Acceptance criteria

- [ ] `/hazard` returns a complete `ENGINE_TIMELINE_RESULT` for at least one hazard type end to end before frontend polish begins.
- [ ] Slider dragging never triggers a backend call; only release does.
- [ ] The frontend never imports or calls `pgmpy`/`networkx` directly — only the two documented endpoints.
- [ ] Full timeline response time is measured and recorded; a fallback plan exists if it exceeds the target in §8.
