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

## Detailed Layer Specifications

### 1. Data Processing Layer

The data processing layer ingests delivery metrics, sanitizes operational observations, and structures them into discrete state spaces required for Bayesian conditional probability modeling:

- **Data Cleaning**: Imputation of missing weather, traffic, and shipment density observations.
- **Feature Engineering**: Computation of geospatial road distances, node transit capacities, and speed ratios.
- **Variable Discretization**: Continuous environmental variables are mapped into discrete states:
  - *Weather*: Clear, Rainy, Stormy
  - *Traffic Density*: Low, Medium, Jammed
  - *Vehicle Condition*: Good, Degraded
  - *Delivery Load*: Normal, High
- **Delivery Outcome Formulation**: Classification of delivery outcomes into *On-Time*, *Minor Delay*, and *Severe Delay*.

---

### 2. Probabilistic Modeling Layer

This layer models probabilistic dependencies between operational hazards and logistics network performance:

- **Bayesian Network (BN)**: Represents conditional dependencies between root hazard causes (weather, traffic, vehicle state) and intermediate node-level delay risks.
- **Two-Time-Slice Dynamic Bayesian Network (DBN)**: Extends static inference to temporal dynamics ($t_0 \to t_1$), capturing disruption persistence and post-disruption recovery across consecutive operational periods.
- **Path-Centric Correlated Uncertainty**: Partitions network edges into macro corridors (following PACE / SPOTAR principles), avoiding naive independent-edge assumptions and capturing correlated spatial disruptions.
- **Continuous Fat-Tailed Delays**: Incorporates Jones & Faddy Skew-t and Skew-Normal distributions to accurately reflect asymmetric delay distributions observed during extreme weather events.

---

### 3. Probabilistic Inference Layer

When external operational conditions change or localized disruption reports arrive:

- **Evidence Ingestion**: Dynamic assignment of observed evidence $\mathbf{E} = \{X_1 = e_1, X_2 = e_2, \dots\}$.
- **Belief Propagation**: Exact marginal updating via **Variable Elimination** computes posterior probabilities:
  $$P(\text{Delay} \mid \mathbf{E}) \quad \text{and} \quad P(\text{On-Time} \mid \mathbf{E})$$
- **Dynamic State Transition**: DBN forward-filtering projects future disruption probabilities across time horizons.

---

### 4. Physical Logistics Network Layer

ProbRoute models multi-echelon supply chain infrastructures across two concrete topologies:

#### A. 20-Node Hierarchical Physical Grid (Coursework Pipeline)
- **1 Central Warehouse**: Primary shipment origination node.
- **18 Multi-Tier Hubs**: Regional hubs (RH1–RH3), transit hubs (TH1–TH9), and local distribution hubs (LH1–LH3).
- **1 Delivery Zone**: Terminal customer delivery region.
- **Bidirectional Arteries**: Inter-hub cross-links representing alternative rerouting avenues.

#### B. 43-Node Real-World Tamil Nadu Hierarchy (Extended Spatial Engine)
- **3 Strategic Headquarters**: Chennai Central HQ, Coimbatore Western HQ, Madurai Southern HQ.
- **10 Regional Hubs**: Key transit intersections including Tiruchirappalli, Salem, Vellore, Tirunelveli, Erode, and Thoothukudi Maritime Port Hub.
- **30 District Warehouses**: Granular distribution nodes covering major industrial and agricultural centers.
- **128 Directed Edges**: Real-world highway topology mapped across 8 macro arterial corridors (NH44, NH48, NH32, NH544, etc.).

---

### 5. Risk Propagation Layer

Inferred delay probabilities from the probabilistic layer are mapped onto the physical topology:

- **Node Risk Scoring**: Each hub is evaluated for congestion vulnerability based on incoming traffic beliefs and storage capacities.
- **Edge Hazard Weighting**: Transportation connections inherit hazard exposures from their respective macro corridors and localized environmental cells.
- **Vulnerability Diagnostics**: Identifies critical single points of failure where localized disruptions risk cascading across the broader logistics network.

---

### 6. Route Resilience & Decision Layer

Rather than relying on static Dijkstra shortest paths, ProbRoute solves the **Reliable Shortest Path Problem (RSPP)**:

- **RSPP-A\* Heuristic Search**: Multi-criteria search simultaneously optimizing for:
  1. Expected Travel Time ($\mathbb{E}[T]$)
  2. Disruption Exposure ($R_{\text{exposure}}$)
  3. $\alpha$-Reliability ($P(T \le T_{\text{budget}}) \ge \alpha$)
- **First-Order Stochastic Dominance (FSD) Pruning**: Dynamically prunes non-Pareto candidate paths, eliminating high-risk sub-paths early and maintaining low search latencies.
- **Pareto Recommendation**: Presents trade-off alternatives and highlights the single most resilient route under prevailing evidence.

---

### 7. Resilience Metric Scorecard

Evaluates routes using the 5 core resilience dimensions defined by **Jiang et al. (2020)**:

| Resilience Dimension | Operational Definition | System Metric |
|---|---|---|
| **1. Absorptive Capacity** | Ability to withstand shocks without operational failure | Probability of on-time delivery despite active disruptions |
| **2. Restorative Capacity** | Speed of returning to nominal operational capacity | DBN recovery rate across consecutive time slices |
| **3. Adaptive Capacity** | Flexibility to reroute around degraded nodes | Availability of alternative Pareto-optimal paths |
| **4. Redundancy** | Structural diversity of alternative routes | Number of independent non-overlapping corridor alternatives |
| **5. Rapidity** | Timeliness of route adaptation and dispatch | Algorithmic execution latency of rerouting decisions |

---

### 8. Benchmark Suite & Performance Verification

The system was formally verified on the 43-node Tamil Nadu network to ensure real-time interactive decision support:

| Verification Task | Target Specification | Measured Result | Evaluation |
|---|---|---|---|
| **pgmpy DBN Inference Latency** | $< 1500.0\text{ ms}$ (10 frames) | **$22.61\text{ ms}$** ($2.05\text{ ms/frame}$) | **PASS** |
| **Vectorized NumPy Fallback Speed** | High-fps UI timeline scrubbing | **$0.230\text{ ms}$** ($105.1\times$ speedup) | **PASS** |
| **RSPP-A\* Multi-Criteria Latency** | $< 300.0\text{ ms}$ (HQ_Chennai $\to$ WH_30) | **$0.65\text{ ms}$** | **PASS** |
| **FSD Dominance Pruning Efficiency** | High search space reduction | **$65.7\%$** candidates pruned | **PASS** |
| **Geospatial Graph Integrity** | 43 nodes, strong connectivity | $100\%$ reachability, $0$ isolated nodes | **PASS** |

---

# Repository Structure

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

# Execution & Usage Guide

### 1. Prerequisites & Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Vilasith-c/Resilient-Route-Decision-Support-in-Uncertain-Logistics-Network.git
cd Resilient-Route-Decision-Support-in-Uncertain-Logistics-Network
pip install -r requirements.txt
```

### 2. Launch the Streamlit Interactive Dashboard

Run the primary decision-support dashboard (PRDs 1–7):

```bash
streamlit run app.py
```

### 3. Launch the Phase 2 FastAPI REST Service

Start the backend server for spatial hazard simulation and GeoJSON delivery (PRDs 8–10):

```bash
cd phase2_tamil_nadu_engine
uvicorn main:app --reload --port 8000
```
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

### 4. Run Test & Benchmark Suites

Run automated unit and integration tests:

```bash
python -m pytest
```

Execute the Phase 1 benchmark verification suite:

```bash
python phase2_tamil_nadu_engine/phase1_benchmark.py
```
