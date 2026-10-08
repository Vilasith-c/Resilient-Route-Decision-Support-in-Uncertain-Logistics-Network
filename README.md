# ProbRoute: Probabilistic Route Resilience for Uncertain Logistics Networks

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**ProbRoute** is an uncertainty-aware logistics decision-support framework that evaluates freight corridors and transportation delivery routes under volatile, disruptive operational conditions. Combining **Dynamic Bayesian Networks (DBNs)**, **path-centric corridor dependency models (SPOTAR / PACE)**, and **RSPP-A\* multi-criteria heuristic search with First-Order Stochastic Dominance (FSD) pruning**, ProbRoute identifies vulnerable infrastructure and recommends resilient, Pareto-optimal routing strategies in real time.

---

## Table of Contents

- [Overview & Objectives](#overview--objectives)
- [System Architecture](#system-architecture)
- [The 8-Stage Algorithmic Pipeline](#the-8-stage-algorithmic-pipeline)
- [Theoretical & Mathematical Foundations](#theoretical--mathematical-foundations)
- [Repository Structure](#repository-structure)
- [Quick Start: Full Stack Setup](#quick-start-full-stack-setup)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Start the FastAPI Backend](#2-start-the-fastapi-backend)
  - [3. Start the React + Vite Frontend](#3-start-the-react--vite-frontend)
  - [4. Alternative: Streamlit Dashboard](#4-alternative-streamlit-dashboard)
- [Interactive Simulation Guide (Web UI)](#interactive-simulation-guide-web-ui)
- [Backend REST API Reference](#backend-rest-api-reference)
- [Formal Benchmark & Verification Results](#formal-benchmark--verification-results)
- [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## Overview & Objectives

Traditional logistics routing algorithms typically optimize static metrics (nominal Euclidean distance or minimum travel time). However, real-world networks face acute disruptions—cyclones, coastal flash floods, severe monsoon events, infrastructure failures, and labor strikes. A route that appears optimal in clear weather can become completely blocked or experience severe fat-tailed delays during localized shocks.

**ProbRoute** resolves this limitation by:
1. **Modeling Correlated Uncertainty**: Partitioning routes into arterial macro-corridors to capture spatial correlation rather than assuming edge independence.
2. **Propagating Beliefs Temporally**: Employing a Dynamic Bayesian Network (DBN) across time slices $t_0, \dots, t_H$ to track shock onset, contagion, and infrastructure recovery.
3. **Evaluating 5-Dimensional Resilience**: Quantifying system recovery using the **Jiang et al. (2020)** scorecard (Absorptive, Restorative, Adaptive capacities, Redundancy, Rapidity).
4. **Providing Real-Time Pareto Optimization**: Running RSPP-A\* heuristic search with FSD pruning to return candidate trade-offs between expected transit time and $\alpha$-reliability ($P(T \le T_{\text{budget}}) \ge \alpha$).

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL EVIDENCE & HAZARD                         │
│                                                                             │
│   Spatial Epicenter (Lat, Lon) | Hazard Radius | Intensity | Hazard Type    │
│   (Cyclone, Monsoon Flood, Heatwave, Infrastructure Failure, Labor Strike)  │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  SPATIAL HAZARD INTERCEPTION & EXPOSURE                     │
│                                                                             │
│   Haversine Distance Mapping ──► Gaussian/Linear Attenuation Decay          │
│   Node-level Hazard Interception & Macro Highway Corridor Exposure Weights   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DYNAMIC BAYESIAN NETWORK (DBN) LAYER                    │
│                                                                             │
│   Time-Slice Belief Propagation:  t_0  ──────►  t_1  ──────►  ...  ──►  t_H  │
│   • Inter-slice persistence:  P(State_{t+1} | State_t, Hazard_{t+1})        │
│   • Shock Contagion & Correlated Corridor Failure (PACE / SPOTAR)           │
│   • Endogenous Recovery Dynamics across Time Horizon                         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHYSICAL LOGISTICS NETWORK (43-NODE TAMIL NADU)             │
│                                                                             │
│   • 3 Strategic HQs (Chennai Central, Coimbatore Western, Madurai Southern) │
│   • 10 Regional Transit Hubs (Trichy, Salem, Vellore, Tirunelveli, etc.)    │
│   • 30 District Distribution Warehouses (WH_01 to WH_30)                    │
│   • 128 Directed Arterial Edges across 8 Macro Highway Corridors            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  RSPP-A* MULTI-CRITERIA ROUTING & FSD PRUNING              │
│                                                                             │
│   • Expected Travel Time:  E[T]                                             │
│   • Disruption Exposure Risk:  R_exposure                                   │
│   • Alpha-Reliability:  P(T <= T_budget) >= alpha                           │
│   • First-Order Stochastic Dominance (FSD) candidate pruning                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RESILIENCE EVALUATION & DECISION                       │
│                                                                             │
│   • Jiang et al. (2020) 5-Capability Scorecard (Absorptive, Restorative...) │
│   • Recommended Primary Resilient Route & Alternative Pareto Choices        │
│   • Unified REST API (FastAPI) & Interactive Geospatial Dashboard (React)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The 8-Stage Algorithmic Pipeline

ProbRoute executes an 8-stage pipeline conforming strictly to PRDs 1–10:

1. **Stage 1: Network Construction**  
   Initializes the 43-node geospatial topology (3 HQs, 10 Hubs, 30 Warehouses, 128 directed edges) covering Tamil Nadu with real-world GPS coordinates and verified strong connectivity.
2. **Stage 2: Uncertainty Modeling (PACE / SPOTAR Corridors)**  
   Maps physical edges to 8 arterial corridors (NH44 North-South, NH48 Golden Quadrilateral, NH32 Coastal, NH544 Industrial, etc.), modeling intra-corridor failure correlation.
3. **Stage 3: Fat-Tailed Delay Distributions**  
   Fits Jones & Faddy Skew-t and Skew-Normal distributions to empirical transit times, capturing heavy-tailed delivery delays during disruption.
4. **Stage 4: Spatial Hazard Interception**  
   Calculates continuous spatial exposure scores $[0, 1]$ for every node and corridor based on haversine distance to the hazard epicenter and radius falloff.
5. **Stage 5: DBN Belief Propagation across Time Horizon ($t_0 \dots t_H$)**  
   Executes forward filtering across time slices, generating dynamic state distributions (`Nominal`, `Warning`, `Degraded`, `Critical/Offline`).
6. **Stage 6: Reliability Ranking via RSPP-A\***  
   Solves the Reliable Shortest Path Problem using A\* search paired with First-Order Stochastic Dominance (FSD) to filter dominated route alternatives.
7. **Stage 7: Resilience Metric Scoring (Jiang et al. 2020)**  
   Quantifies the 5 core resilience dimensions: Absorptive, Restorative, Adaptive capacities, Redundancy, and Rapidity.
8. **Stage 8: Unified Payload Assembly (`ENGINE_TIMELINE_RESULT`)**  
   Bundles timeline frames, node states, corridor statuses, recommended routes, and resilience metrics into a single response consumed by the frontend.

---

## Theoretical & Mathematical Foundations

### 1. Two-Time-Slice Dynamic Bayesian Network (2-TBN)
For node/corridor state $S_t \in \{\text{Nominal}, \text{Warning}, \text{Degraded}, \text{Critical}\}$ and external hazard exposure $H_t$:
$$P(S_t \mid S_{t-1}, H_t)$$
The transition probability combines:
- **Disruption Persistence**: Probability that degraded infrastructure remains degraded in subsequent time frames.
- **Shock Onset**: Probability that localized exposure triggers a state downgrade.
- **Restorative Recovery**: Gradual return to nominal state as time elapses past peak hazard intensity.

### 2. Reliable Shortest Path (RSPP-A\*) & Stochastic Dominance
Given candidate paths $p_1, p_2$ with travel time distributions $F_{p_1}(t)$ and $F_{p_2}(t)$:
- **First-Order Stochastic Dominance (FSD)**: Path $p_1$ stochastically dominates $p_2$ ($p_1 \succeq_{\text{FSD}} p_2$) if:
  $$F_{p_1}(t) \ge F_{p_2}(t) \quad \forall t \ge 0$$
  with strict inequality for at least one $t$. Any path dominated by an existing candidate is pruned immediately from the priority queue.
- **$\alpha$-Reliability Objective**:
  $$\max \quad \alpha \quad \text{s.t.} \quad P(T_p \le T_{\text{budget}}) \ge \alpha$$

### 3. Jiang et al. (2020) 5-Capability Scorecard
| Capability | Formulation | Meaning |
|---|---|---|
| **Absorptive Capacity** | $\frac{1}{N}\sum_{i=1}^{N} P(S_{i, t} \ne \text{Critical})$ | Ability to withstand the initial hazard impact |
| **Restorative Capacity** | $\frac{\Delta \text{Absorptive}}{\Delta t} \text{ for } t > t_{\text{peak}}$ | Speed and extent of autonomous recovery |
| **Adaptive Capacity** | $\frac{|\text{Pareto Routes}|}{|\text{Total Feasible Routes}|}$ | Flexibility to reroute around damaged bottlenecks |
| **Redundancy** | $1 - \frac{|\bigcap \text{Edges}(p_k)|}{|\bigcup \text{Edges}(p_k)|}$ | Corridor independence and structural diversity |
| **Rapidity** | $\frac{1}{1 + \tau_{\text{compute}}}$ | Latency of algorithmic rerouting recommendation |

---

## Repository Structure

```text
.
├── app.py                             # Streamlit dashboard entry point (PRDs 1-7)
├── README.md                          # Comprehensive project documentation
├── requirements.txt                   # Complete Python backend dependencies
│
├── components/                        # Streamlit visual components
│   ├── evidence_panel.py              # Sliders and hazard controls
│   ├── network_map.py                 # NetworkX / PyVis graph rendering
│   ├── resilience_panel.py            # Streamlit resilience scorecard
│   └── route_table.py                 # Route comparison tables
│
├── frontend/                          # Phase 3 Interactive React + Vite Dashboard
│   ├── index.html                     # HTML entry point
│   ├── package.json                   # NPM dependencies (React 19, Vite, Tailwind v4, Leaflet)
│   ├── vite.config.ts                 # Dev server configuration with /api backend proxy
│   └── src/
│       ├── App.tsx                    # Main dashboard application logic & state
│       ├── main.tsx                   # React root mount
│       ├── components/
│       │   ├── Header.tsx             # System branding & real-time connection status
│       │   ├── NetworkMap.tsx         # Interactive Leaflet map with multi-basemap switcher
│       │   ├── HazardControlPanel.tsx # Hazard parameter sliders & timeline playback bar
│       │   └── ResilienceRoutePanel.tsx # RSPP-A* routes & Jiang et al. resilience scorecard
│       ├── services/
│       │   └── api.ts                 # REST API client connecting to FastAPI backend
│       └── types/
│           └── network.ts             # TypeScript definitions for GeoJSON, DBN, and timeline
│
├── inference_engine/                  # Baseline inference pipeline
│   ├── engine.py                      # Core inference orchestration
│   ├── engine_state.py                # State management
│   ├── inference_runner.py            # Batch execution runner
│   ├── report_generator.py            # PDF / text report generation
│   └── tests/test_inference.py        # Automated test suite
│
├── model_layer/                       # Probabilistic mathematical models
│   ├── corridor_model.py              # Macro corridor definitions
│   ├── dbn_model.py                   # Dynamic Bayesian Network (pgmpy)
│   ├── graph_builder.py               # 20-node benchmark grid builder
│   ├── reliability_ranking.py         # RSPP-A* search implementation
│   └── resilience_metrics.py          # 5 resilience dimension calculators
│
├── phase2_tamil_nadu_engine/          # Phase 2: 43-Node Real-World Engine
│   ├── main.py                        # FastAPI REST API (/health, /network, /hazard)
│   ├── orchestrator.py                # 8-stage simulation orchestrator & timeline builder
│   ├── hazard_exposure.py             # Haversine spatial hazard exposure calculator
│   ├── corridor_model.py              # 8 Tamil Nadu macro highway corridors
│   ├── delay_distribution.py          # Skew-t travel time priors
│   ├── phase1_benchmark.py            # Formal latency & benchmark verification suite
│   └── phase1_report.json             # Verification results JSON artifact
│
└── docs/                              # Architecture documentation & literature
    ├── prds/                          # PRDs 01 through 10
    └── papers/                        # Reference literature & foundational papers
```

---

## Quick Start: Full Stack Setup

### 1. Prerequisites

- **Python**: 3.9, 3.10, or 3.11 installed
- **Node.js**: v18+ or v20+ with `npm`
- **Git**

Install the Python dependencies:

```powershell
pip install -r requirements.txt
```

---

### 2. Start the FastAPI Backend

Open a terminal and start the backend service on port `8000`:

```powershell
# Navigate to the Phase 2 engine directory
cd "phase2_tamil_nadu_engine"

# Start the server with hot-reload enabled
uvicorn main:app --reload --port 8000
```

Verify that the backend is running:
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

> [!TIP]
> If you encounter `[WinError 10013]` on Windows, port 8000 is already in use by another process. Run `Get-NetTCPConnection -LocalPort 8000` to find the process ID and terminate it with `Stop-Process -Id <PID> -Force`.

---

### 3. Start the React + Vite Frontend

In a **second terminal**:

```powershell
# Navigate to the frontend directory
cd "frontend"

# Install NPM packages (only needed once)
npm install

# Start the Vite development server
npm run dev
```

Open your browser at **[http://localhost:5173/](http://localhost:5173/)**.

The Vite development server automatically proxies all `/api/*` calls directly to `http://127.0.0.1:8000/*`, eliminating CORS issues during development.

---

### 4. Alternative: Streamlit Dashboard

If you prefer running the single-process Streamlit interface (PRDs 1–7):

```powershell
streamlit run app.py
```

---

## Interactive Simulation Guide (Web UI)

Once both the backend and frontend are running at `http://localhost:5173/`:

```
┌───────────────────────┬───────────────────────────────────┬───────────────────────┐
│ HAZARD CONTROLLER     │       INTERACTIVE LEAFLET MAP     │ RESILIENCE SCORECARD  │
│                       │                                   │                       │
│ • Select Hazard Type  │ • 43 Nodes (3 HQs, 10 Hubs, 30 WH)│ • RSPP-A* Route Info  │
│ • Sliders (Radius/    │ • 128 Edges / 8 Corridors         │   (Travel time, alpha,│
│   Intensity/Horizon)  │ • Free Basemap Switcher:          │    disruption risk)   │
│ • Click Map to place  │   (Dark Canvas / OSM / Satellite) │ • Jiang et al. (2020) │
│   hazard epicenter    │ • Pulsating hazard radius circle  │   5 Capabilities      │
│ • "Run Simulation"    │ • Click any node for popup specs  │ • Candidate Route     │
│                       │                                   │   Alternatives        │
├───────────────────────┴───────────────────────────────────┴───────────────────────┤
│                   TIMELINE SCRUBBER & PLAYBACK (t = 0 to t = 10)                  │
│                   [Play / Pause]  ◄──●────────────────────────►                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

1. **Place the Hazard**:
   - In the **Spatial Hazard Controller** (left panel), choose a hazard type (`Cyclone`, `Flood`, `Heatwave`, `Infrastructure Failure`, or `Labor Strike`).
   - Adjust the **Radius** (e.g. 50 km), **Intensity** ($0.1 \to 1.0$), and **Time Horizon** ($t = 1 \to 15$ slices).
   - Click anywhere on the map to place the hazard epicenter (coordinates update automatically).
2. **Execute Simulation**:
   - Click the **"Run Simulation"** (or **"Inject Hazard"**) button.
   - The backend runs the 8-stage pipeline in $< 30\text{ ms}$ and returns the complete dynamic timeline.
3. **Playback & Timeline Scrubbing**:
   - Use the **Play / Pause** toggle or drag the timeline slider at the bottom.
   - Watch the nodes change state dynamically:
     - 🟢 **Nominal** (Operating normally)
     - 🟡 **Warning** (Minor corridor congestion)
     - 🟠 **Degraded** (High delay probability)
     - 🔴 **Critical / Offline** (Corridor impassable)
4. **Inspect Route Recommendations**:
   - View the highlighted **RSPP-A\* optimal route** displayed on the map in neon sky blue.
   - Review travel time ($\text{hrs}$), on-time reliability ($\alpha$), and disruption probability in the right-hand panel.
   - Select alternative candidate paths to compare trade-offs.

---

## Backend REST API Reference

The FastAPI service exposes three main endpoints:

### 1. `GET /health`
Returns system status, network topologies, and academic model specifications.
```json
{
  "status": "healthy",
  "service": "Tamil Nadu Resilient Logistics Simulator Engine",
  "version": "2.1.0",
  "network": {
    "total_nodes": 43,
    "hqs": 3,
    "hubs": 10,
    "warehouses": 30,
    "directed_edges": 128,
    "macro_corridors": 8
  }
}
```

### 2. `GET /network`
Returns complete network graph topology and a GeoJSON `FeatureCollection` (Point features for nodes, LineString features for highway edges).

### 3. `POST /hazard`
Executes the 8-stage simulation and returns `ENGINE_TIMELINE_RESULT`.

**Request Body:**
```json
{
  "hazard_type": "cyclone",
  "latitude": 11.9401,
  "longitude": 79.7719,
  "radius_km": 50.0,
  "intensity": 0.85,
  "time_horizon": 10
}
```

**Response Body:**
```json
{
  "simulation_id": "sim_20261006_210228",
  "time_horizon": 10,
  "frames": [
    {
      "time_slice": 0,
      "node_states": { "HQ_Chennai": "Nominal", "Hub_Cuddalore": "Critical" },
      "corridor_statuses": { "CORR_NH32_COASTAL": "Blocked" },
      "resilience_scorecard": {
        "absorptive_capacity": 0.814,
        "restorative_capacity": 0.120,
        "adaptive_capacity": 0.750,
        "redundancy": 0.680,
        "rapidity": 0.998
      }
    }
  ],
  "primary_rerouted_solutions": [
    {
      "route": "HQ_Chennai -> Hub_Tiruchirappalli -> HQ_Madurai -> WH_30_Nagercoil",
      "travel_time_hr": 14.97,
      "on_time_reliability_alpha": 0.783,
      "disruption_prob": 0.217,
      "hops": 6
    }
  ]
}
```

---

## Formal Benchmark & Verification Results

Measured on the 43-node Tamil Nadu network (`phase2_tamil_nadu_engine/phase1_report.json`):

| Verification Dimension | Target Threshold | Measured Result | Performance Factor | Status |
|---|---|---|---|---|
| **pgmpy DBN Inference Latency** | $< 1500.0\text{ ms}$ (10 frames) | **$24.22\text{ ms}$** | $2.20\text{ ms / frame}$ | **PASS** |
| **Vectorized NumPy Fallback Latency** | Interactive timeline | **$0.23\text{ ms}$** | $105.1\times$ speedup | **PASS** |
| **RSPP-A\* Heuristic Search Time** | $< 300.0\text{ ms}$ (Chennai $\to$ Nagercoil) | **$0.65\text{ ms}$** | $461\times$ under budget | **PASS** |
| **FSD Dominance Pruning Efficiency** | Reduction of candidate search space | **$65.7\%$** | 46 / 140 paths pruned | **PASS** |
| **Geospatial Graph Integrity** | 43 nodes, $0$ isolated nodes | **$100\%$ Strongly Connected** | 128 edges, 0 isolates | **PASS** |

To re-run the benchmark suite:
```powershell
python phase2_tamil_nadu_engine/phase1_benchmark.py
```

To run automated unit and integration tests:
```powershell
python -m pytest
```

---

## Troubleshooting & FAQs

### Q1: `[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`
- **Cause**: Port `8000` is already held by a running background process.
- **Fix**: Check which process is using port 8000 and terminate it:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
  Stop-Process -Id <OwningProcessId> -Force
  ```
  Then re-run `uvicorn main:app --reload --port 8000`.

### Q2: Frontend shows "Backend: Disconnected"
- Ensure `uvicorn` is active in your backend terminal on port 8000.
- Verify `http://localhost:8000/health` returns status `healthy` in your browser.
- Ensure Vite is running via `npm run dev` in the `frontend` directory. The proxy in `vite.config.ts` handles communication between `5173` and `8000`.

### Q3: Leaflet map tiles fail to load or show watermarks
- ProbRoute uses 100% free, keyless tile providers (Esri Dark Canvas, OpenStreetMap Standard, and Esri World Imagery). No third-party API keys or watermarked CARTO tiles are required. Use the basemap selector in the top-right corner of the map to switch styles.

---

## Authors & Acknowledgments

- **Algorithm & System Architecture**: ProbRoute Development Team
- **Theoretical Foundations**:
  - *Dynamic Bayesian Networks in Logistics*: Wageningen University & Research
  - *RSPP-A\* Heuristic & First-Order Stochastic Dominance*: Chen et al. (2012)
  - *5-Dimensional Supply Chain Resilience Capabilities*: Jiang et al. (2020)
  - *Corridor Correlated Uncertainty*: SPOTAR / PACE (Andonov & Yang)
