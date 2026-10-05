# PRD 8 — What You Need to Bring to the Table

**Project:** Interactive Tamil Nadu Resilient Logistics Simulator (evolution of the Resilient Route Advisor)
**Scope:** 3 headquarters, 10 hubs, 30 warehouses, Tamil Nadu map, click-to-place weather/disaster events with adjustable intensity
**Depends on:** PRD 1–7 (original 8-stage BN pipeline, still the algorithmic core)
**Status:** v1.0

---

## 1. Purpose

Before any code is written, this document lists everything the team needs to have decided, prepared, or set up. Skipping this step is the most common reason a project like this stalls halfway — the team starts building UI before agreeing what a node even is.

## 2. Team skill coverage needed

| Skill area | Needed for | Minimum bar |
|---|---|---|
| Python (FastAPI, `pgmpy`, `networkx`) | Backend + model layer (PRD 5, 6) | At least one person comfortable with this from the original PRDs |
| React + TypeScript | Frontend, map, hazard placement UI | At least one person; this is new relative to the original Streamlit plan (PRD 7) — budget learning time if nobody has it |
| Basic GIS/geo handling | Coordinates, radius math, GeoJSON | Learnable in a day; no dedicated GIS person required at this scale |
| Bayesian network theory | Interpreting/defending CPTs and inference results in the report and viva | Whole team, since this is the course's actual subject |

**Decision needed now:** who owns frontend vs. backend, so PRD 9's build order can be parallelized instead of serialized.

## 3. Data and assets to prepare before coding starts

- **Node list with coordinates.** A finalized table of the 3 HQs, 10 hubs, and 30 warehouses (name, lat, lon, type). Without this, nothing else can start. Use real Tamil Nadu towns; you don't need real facility addresses, only plausible coordinates.
- **Tamil Nadu boundary GeoJSON.** For drawing the state outline under the network. Sourceable from Natural Earth (admin-1 level) or DataMeet — check the license before shipping it in a report/demo.
- **Route geometry between nodes.** Either precomputed via a routing service (OSRM/OpenRouteService) or a haversine-distance-with-circuity-factor fallback (see PRD 9 §5). This must exist before the map can draw meaningful route lines instead of straight lines.
- **Hazard taxonomy for Tamil Nadu specifically.** A short list of hazards that are actually plausible for the region — heavy rain/flood, cyclone, storm surge, heat wave, Western Ghats landslide/road closure, hub outage. Do not reuse generic hazards (e.g. snow) without flagging them as unrealistic for the region.
- **Hazard-effect mapping table.** For each hazard type, how a given intensity (0–100%) degrades a node's or edge's operational probability. This is what turns "60% rain" into an actual number your BN can consume. This table is arguably the single most important artifact the team must agree on before backend work starts — see PRD 9 §5 for its schema.
- **CPT seed assumptions log.** A short written record of every assumption behind your conditional probability tables (e.g., "we assume a cyclone at 70% severity reduces a coastal hub's on-time probability by 40%, based on no historical data — expert judgement only"). This log is what you'll be asked to defend in review; write it as you go, not after.

## 4. Open decisions the team must make before building

| Decision | Options | Recommendation |
|---|---|---|
| Network topology | HQ → hub → warehouse as final destination, vs. a separate delivery-zone node per warehouse cluster | Decide before graph_builder is written — this changes the node/edge schema in PRD 5 |
| Hazard placement granularity | Free click-anywhere with radius, vs. snapping to predefined districts | Free click-anywhere (see PRD 9 §4) — more game-like, matches the stated intent |
| Recompute strategy | Instant recompute on every slider drag, vs. debounced recompute on release | Debounce first; only go instant if latency testing (PRD 8 §6) shows it's fast enough |
| Inference engine | `pgmpy` DBN throughout, vs. `pgmpy` for the static BN and a numpy forward-filter for the time dimension | Prototype both on the 43-node graph before committing (§6) |

## 5. Tools and accounts to set up

- Node.js + npm/yarn, Vite scaffold for the React app
- Python environment with `fastapi`, `pgmpy`, `networkx`, `numpy`, `scipy`
- A routing service account (OpenRouteService free tier) or confirmation that self-hosting OSRM locally is feasible on team hardware
- A map tile provider for the light-mode basemap (e.g. CARTO Positron) — confirm current usage terms before the demo goes live anywhere public
- Git repository with a branch strategy (frontend/backend can diverge and merge at the API contract in PRD 9 §6)

## 6. Feasibility checks to run in week one (do not skip)

1. **BN latency test:** build the 43-node graph with placeholder CPTs, run `pgmpy` inference on it, and time it. If a single inference call exceeds ~300 ms, plan for debouncing or the numpy fallback now, not after the frontend is built around instant updates.
2. **Routing service test:** request routes for ~15 of the ~40 planned edges and confirm the service returns usable geometry within its rate limits.
3. **Map rendering test:** plot 43 markers plus route lines in `react-leaflet` and confirm it renders smoothly before investing in the hazard-placement UI on top of it.

## 7. Non-negotiable scope guardrails

To avoid drifting back toward the abandoned India-wide 625-node plan:

- Node count stays at 43 (3 + 10 + 30) unless a deliberate decision is made to change it.
- No PostGIS, no WebSockets, no Docker deployment — not needed at this scale (per the earlier feasibility review).
- No full-state street-level OSMnx graph — only the abstract node/edge network, with an optional single-city OSMnx zoom-in as a bonus demo, not a dependency.

## 8. Acceptance criteria

- [ ] Node list (3 HQ + 10 hub + 30 warehouse) is finalized with real coordinates before PRD 9's build order begins.
- [ ] Hazard-effect mapping table exists in a reviewable form (spreadsheet or JSON) before backend work starts.
- [ ] All three feasibility checks in §6 have been run and their results recorded, even if the result is "this needs a fallback."
- [ ] CPT assumption log has at least one entry per hazard type before the first demo.
