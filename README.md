# ProbRoute

### Probabilistic Route Resilience for Uncertain Logistics Networks

ProbRoute is an uncertainty-aware logistics decision-support framework that evaluates delivery routes under changing operational conditions and recommends resilient alternatives using probabilistic reasoning.

---

## Overview

Logistics networks operate under uncertainty caused by factors such as traffic congestion, weather conditions, demand fluctuations, vehicle conditions, and operational disruptions. Traditional routing approaches primarily rely on fixed attributes such as distance or travel time and may therefore select routes that are efficient under normal conditions but unreliable when real-world conditions change.

ProbRoute addresses this limitation by combining a data-driven probabilistic reasoning layer with a physical logistics network. The system uses historical delivery data to model uncertainty, performs probabilistic inference when new evidence is observed, maps the resulting risk onto a logistics network containing 20 or more physical nodes, evaluates candidate routes, and recommends the route with the highest resilience under the current conditions.

---

## Problem Statement

Logistics networks operate under uncertainty due to factors such as traffic congestion, weather conditions, demand fluctuations, and operational disruptions. Traditional routing methods often rely on fixed conditions and may therefore select routes that are efficient in normal situations but unreliable under changing conditions. This project addresses the need to evaluate logistics routes probabilistically by considering uncertainty, delivery risk, and route reliability to support resilient logistics decisions.

---

## Project Objective

The objective of ProbRoute is to develop a probabilistic logistics decision-support system that:

- Models uncertainty affecting delivery operations.
- Learns relationships between logistics conditions and delivery outcomes from historical data.
- Performs probabilistic inference based on observed evidence.
- Represents a logistics infrastructure using a network of 20 or more physical nodes.
- Maps inferred risks onto logistics hubs and transportation connections.
- Evaluates candidate routes based on reliability and disruption exposure.
- Identifies vulnerable hubs and high-risk connections.
- Recommends the most resilient route under the current uncertain conditions.

---

# System Architecture at a Glance

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMAZON DELIVERY DATASET                             │
│                                                                             │
│  Weather | Traffic | Vehicle Condition | Multiple Deliveries | Festival    │
│  Location | Distance | Delivery Time                                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA PROCESSING LAYER                               │
│                                                                             │
│  Data Cleaning                                                              │
│  Feature Engineering                                                        │
│  Distance Calculation                                                       │
│  Variable Discretization                                                    │
│  Delivery Outcome Preparation                                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROBABILISTIC MODELING LAYER                             │
│                                                                             │
│                        PRIMARY MODEL:                                       │
│                         BAYESIAN NETWORK                                    │
│                                                                             │
│       Weather ───────┐                                                      │
│       Traffic ───────┤                                                      │
│       Vehicle ───────┼──────► Delivery Risk ──────► Delivery Outcome       │
│       Festival ──────┤                                                      │
│       Delivery Load ─┤                                                      │
│       Distance ──────┘                                                      │
│                                                                             │
│  Models probabilistic dependencies between uncertain logistics variables    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROBABILISTIC INFERENCE LAYER                           │
│                                                                             │
│                         CURRENT EVIDENCE                                    │
│                                                                             │
│          Weather | Traffic | Festival | Vehicle | Delivery Load             │
│                                   │                                         │
│                                   ▼                                         │
│                         BELIEF UPDATING                                     │
│                                   │                                         │
│                  ┌────────────────┴────────────────┐                        │
│                  ▼                                 ▼                        │
│           Delay Probability              On-Time Probability                │
│                                                                             │
│           Operational Risk               Congestion Risk                     │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Probabilistic Risk Mapping
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHYSICAL LOGISTICS NETWORK LAYER                         │
│                                                                             │
│                       20+ PHYSICAL NODES                                    │
│                                                                             │
│        Warehouse → Regional Hubs → Transit Hubs → Delivery Zones            │
│                                                                             │
│              [Warehouse]                                                    │
│                   │                                                         │
│          ┌────────┼────────┐                                                │
│          ▼        ▼        ▼                                                │
│        [RH1]    [RH2]    [RH3]                                              │
│          │ \      │      / │                                                │
│          │  \     │     /  │                                                │
│        [TH1]───[TH2]───[TH3]                                                │
│          │       │       │                                                  │
│        [TH4]───[TH5]───[TH6]                                                │
│          │       │       │                                                  │
│        [TH7]───[TH8]───[TH9]                                                │
│          │       │       │                                                  │
│        [LH1]────[LH2]────[LH3]                                             │
│          │       │       │                                                  │
│        [DZ1]    [DZ2]    [DZ3]                                              │
│                                                                             │
│  Nodes = Physical logistics locations                                       │
│  Edges = Transportation connections                                         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RISK PROPAGATION LAYER                              │
│                                                                             │
│     Probabilistic Inference Results                                         │
│                    │                                                        │
│                    ▼                                                        │
│     Update Hub Risk and Edge Risk                                           │
│                    │                                                        │
│                    ▼                                                        │
│     Identify High-Risk Connections and Vulnerable Hubs                      │
│                    │                                                        │
│                    ▼                                                        │
│     Evaluate Risk Exposure Across Candidate Routes                          │
│                                                                             │
│  Example:                                                                   │
│  Weather Change → Traffic Risk → Hub Congestion → Route Delay Risk          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ROUTE RESILIENCE AND DECISION LAYER                       │
│                                                                             │
│              Route A        Route B        Route C                          │
│                 │              │              │                             │
│                 ▼              ▼              ▼                             │
│          Evaluate Risk   Evaluate Risk   Evaluate Risk                      │
│          Evaluate Time   Evaluate Time   Evaluate Time                      │
│          Evaluate        Evaluate        Evaluate                           │
│          Reliability     Reliability     Reliability                        │
│                 │              │              │                             │
│                 └──────────────┼──────────────┘                             │
│                                ▼                                            │
│                    COMPARE CANDIDATE ROUTES                                 │
│                                │                                            │
│                                ▼                                            │
│                   SELECT MOST RESILIENT ROUTE                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FINAL OUTPUT                                   │
│                                                                             │
│  Recommended Resilient Route                                                │
│  Route-Level Delay Probability                                              │
│  On-Time Delivery Probability                                               │
│  Route Reliability Score                                                    │
│  Vulnerable Hubs                                                            │
│  High-Risk Transportation Connections                                       │
│  Explanation of the Route Recommendation                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```text
.
├── app.py                             # Streamlit Dashboard application entry point (PRDs 1-7)
├── components/                        # Streamlit UI visual components
│   ├── evidence_panel.py              # Interactive evidence injection sliders/toggles
│   ├── network_map.py                 # Graph & routing visualizer (NetworkX + PyVis)
│   ├── resilience_panel.py            # Jiang et al. (2020) 5-dimensional resilience dashboard
│   └── route_table.py                 # Candidate route comparison table & Alpha-reliability ranking
├── inference_engine/                  # Business logic & inference coordination
│   ├── engine.py                      # Core inference orchestration
│   ├── engine_state.py                # State management across evidence updates
│   ├── inference_runner.py            # Batch & sequential inference executor
│   ├── report_generator.py            # Automated PDF/text summary report generation
│   └── tests/                         # Pytest test suite for inference pipeline
├── model_layer/                       # Academic modeling algorithms (PRD 5)
│   ├── corridor_model.py              # Path-centric correlated uncertainty corridors
│   ├── dbn_model.py                   # 2-time-slice Dynamic Bayesian Network (pgmpy)
│   ├── delay_distribution.py          # Skew-t / Skew-Normal travel time distributions
│   ├── graph_builder.py               # Logistics network graph generator (20-node benchmark)
│   ├── reliability_ranking.py         # RSPP-A* multi-criteria search & FSD dominance pruning
│   └── resilience_metrics.py          # 5 resilience dimensions (Absorptive, Restorative, etc.)
├── phase2_tamil_nadu_engine/          # Phase 2: 43-Node Real-World Tamil Nadu Simulator (PRDs 8-10)
│   ├── main.py                        # FastAPI REST API serving GeoJSON & simulation timeline
│   ├── orchestrator.py                # 8-stage simulation orchestrator & timeline generation
│   ├── hazard_exposure.py             # Spatial hazard exposure calculator (Gaussian/linear falloff)
│   ├── corridor_model.py              # 8 Tamil Nadu macro highway corridors (NH44, NH48, etc.)
│   ├── delay_distribution.py          # Empirical travel time distributions
│   ├── phase1_benchmark.py            # Formal latency & algorithmic benchmark suite
│   └── phase1_report.json             # Benchmark verification JSON report
├── docs/                              # Project documentation & references
│   ├── prds/                          # Product Requirement Documents (PRD 01 to PRD 10)
│   └── papers/                        # Reference literature & foundational papers
├── requirements.txt                   # Complete project dependencies
└── .gitignore                         # Git exclusion rules (pycache, envs, artifacts)
```

---

## Theoretical & Algorithmic Foundations

1. **Path-Centric Correlated Uncertainty**: Macro corridor partitioning modeling correlated disruptions (adverse weather, regional strikes, expressway congestion) rather than assuming edge-independence.
2. **Asymmetric Delay Distributions**: Skew-Normal and Skew-t distributions capturing fat-tailed travel delays rather than naive Gaussian assumptions.
3. **Dynamic Bayesian Network (DBN)**: Two-time-slice DBN transitioning from baseline $t_0$ to disrupted state $t_1$, updating marginal beliefs via Variable Elimination.
4. **Reliable Shortest Path Problem (RSPP-A*)**: Hand-crafted multi-criteria search incorporating First-Order Stochastic Dominance (FSD) dominance pruning for $\alpha$-reliable path ranking.
5. **Resilience Scorecard (Jiang et al. 2020)**: Quantifies five core dimensions:
   - Absorptive Capacity
   - Restorative Capacity
   - Adaptive Capacity
   - Redundancy
   - Rapidity

---

## Benchmark Suite Verification (Phase 1)

The Phase 1 verification suite confirms strict compliance with low-latency interactive simulation constraints:

| Task / Metric | Target Criterion | Measured Benchmark | Status |
|---|---|---|---|
| **pgmpy DBN Inference Latency** | $< 1500.0\text{ ms}$ (10 frames) | **$22.6\text{ ms}$** ($2.05\text{ ms/frame}$) | **PASS** |
| **Vectorized NumPy Fallback Speed** | High-fps UI scrubbing | **$0.23\text{ ms}$** ($105\times$ speedup) | **PASS** |
| **RSPP-A\* Latency (HQ $\to$ WH)** | $< 300.0\text{ ms}$ | **$0.65\text{ ms}$** | **PASS** |
| **FSD Dominance Pruning Efficiency** | High search efficiency | **$65.7\%$** paths pruned | **PASS** |
| **Tamil Nadu Geospatial Graph** | 43 nodes, strong connectivity | $100\%$ reachability, $0$ isolated nodes | **PASS** |

---

## Getting Started

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Vilasith-c/Resilient-Route-Decision-Support-in-Uncertain-Logistics-Network.git
cd Resilient-Route-Decision-Support-in-Uncertain-Logistics-Network
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard (PRDs 1–7)

Launch the interactive 20-node logistics decision support dashboard:

```bash
streamlit run app.py
```

### 3. Run the Phase 2 Tamil Nadu Backend Service (PRDs 8–10)

Launch the FastAPI REST API:

```bash
cd phase2_tamil_nadu_engine
uvicorn main:app --reload --port 8000
```
Interactive API documentation is accessible at `http://localhost:8000/docs`.

### 4. Run the Benchmarks & Tests

Run the unit tests:
```bash
python -m pytest
```

Run the Phase 1 benchmark verification suite:
```bash
python phase2_tamil_nadu_engine/phase1_benchmark.py
```
