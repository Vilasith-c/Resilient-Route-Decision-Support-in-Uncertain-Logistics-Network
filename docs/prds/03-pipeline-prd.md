# PRD 3 — Pipeline

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 1 (Paper Analysis), PRD 2 (Idea Statement + Algorithm)
**Status:** v1.0

---

## 1. Purpose

This document specifies the eight-stage conceptual pipeline of the project — the "what happens, in what order, using what technique" — independent of any implementation technology (that is PRDs 5–7). Each stage below lists its purpose, input, output, the exact paper/technique it uses, and the data structure that carries information to the next stage.

## 2. Pipeline overview

```
1. Network Definition
        |
2. Uncertainty Modeling (path-centric)
        |
3. Delay Distribution (skew-t)
        |
4. Probabilistic Propagation (BN inference)
        |
5. Dynamic Belief Updates (two-time-slice DBN)
        |
6. Reliability Ranking (pruned alpha-reliable search)
        |
7. Resilience Scoring (five capabilities)
        |
8. Final Report (recommended resilient route)
```

## 3. Stage-by-stage specification

### Stage 1 — Network Definition
- **Purpose:** Formalize the physical logistics network.
- **Input:** Raw description of nodes (warehouse, 18 hubs, delivery zone) and their physical connections.
- **Output:** Directed graph *G = (N, E)* with base travel time and base disruption probability attached to every edge.
- **Technique/paper:** Chen et al. (2012) node/link/α-reliable-path notation (PRD 1 §3.1).
- **Data structure carried forward:** Graph object (nodes, edges, edge attributes).

### Stage 2 — Uncertainty Modeling (path-centric)
- **Purpose:** Replace the naive assumption that every edge's delay is independent with a model that captures shared disruption exposure between adjacent hubs (e.g., the same storm cell hitting a whole grid row).
- **Input:** Graph from Stage 1.
- **Output:** A set of *corridors* — groups of edges sharing a joint disruption-exposure variable — layered onto the graph.
- **Technique/paper:** SPOTAR / PACE path-centric dependency model, Andonov & Yang (PRD 1 §3.2).
- **Data structure carried forward:** Graph + corridor-to-edge mapping.

### Stage 3 — Delay Distribution
- **Purpose:** Replace the normal-distribution assumption for edge/corridor delay with a distribution that matches real disruption behavior (skewed, heavy-tailed).
- **Input:** Corridor structure from Stage 2.
- **Output:** A fitted skew-t distribution per corridor, discretized into categorical delay states (Low / Medium / High) for use in discrete BN conditional probability tables.
- **Technique/paper:** Metro post-disruption travel-time skew-t model (PRD 1 §3.7).
- **Data structure carried forward:** Per-corridor discretized CPT seed values.

### Stage 4 — Probabilistic Propagation
- **Purpose:** Given a piece of evidence (e.g., "Hub 4 congestion = High"), recompute the posterior probability of every dependent variable in the network — this is the "Delay Probability" / "On-Time Probability" update from the baseline PPT.
- **Input:** BN structure (nodes = corridor/hub/edge states, CPTs from Stage 3), evidence.
- **Output:** Posterior probability distribution over delay/on-time state for every node.
- **Technique/paper:** BN forward and backward inference theory, Hosseini & Ivanov (PRD 1 §3.3).
- **Data structure carried forward:** Posterior probability table (per node, per state).

### Stage 5 — Dynamic Belief Updates
- **Purpose:** Instead of recomputing the full posterior from scratch every time new evidence arrives, maintain a continuously updating belief across time — this is what makes the system "live" rather than one-shot.
- **Input:** BN from Stage 4, evidence stream over time.
- **Output:** A two-time-slice DBN where slice *t+Δt*'s state depends on both its own-time-slice parents and its state/parents at time *t*.
- **Technique/paper:** Two-time-slice Dynamic Bayesian Network, Jiang et al. (PRD 1 §3.5); directly implements the "online forecasting" extension explicitly named as future work by the metro paper (PRD 1 §3.7).
- **Data structure carried forward:** Time-indexed posterior sequence.

### Stage 6 — Reliability Ranking
- **Purpose:** Rank candidate routes by reliability without brute-force enumeration of every possible path.
- **Input:** Posterior delay probabilities (Stage 4/5) mapped onto candidate paths in the graph.
- **Output:** A pruned, ranked list of non-dominated candidate routes and their α-reliable travel-time budgets.
- **Technique/paper:** RSPP-LS / RSPP-A* label-setting algorithms with first-order stochastic dominance (FSD) pruning, Chen et al. (2012) (PRD 1 §3.1).
- **Data structure carried forward:** Ranked route list with reliability scores.

### Stage 7 — Resilience Scoring
- **Purpose:** Go beyond a single route's reliability score to characterize the *network's* resilience — which hub/edge is the weakest point, and how well the network recovers after a disruption.
- **Input:** Ranked routes (Stage 6), full posterior history (Stage 5).
- **Output:** Five resilience-capability scores per network segment: rapid response, sustained resistance, continuous running, rapid convergence, dynamic evolution.
- **Technique/paper:** Five-capability DBN resilience quantification, Jiang et al. (PRD 1 §3.5).
- **Data structure carried forward:** Resilience capability scorecard + flagged vulnerable hub/edge.

### Stage 8 — Final Report
- **Purpose:** Package everything into the deliverable the baseline PPT already promised.
- **Input:** Ranked routes (Stage 6), resilience scorecard (Stage 7).
- **Output:** Probabilistic Logistics Resilience Report containing: comparison table (delay probability / on-time probability / reliability rating per route), flagged vulnerable hub and high-risk edge, recommended route with plain-language justification.
- **Technique/paper:** Baseline project deliverable (unchanged).
- **Data structure carried forward:** N/A — terminal stage; rendered to user (PRD 7) and exported (PRD 6).

## 4. Stage dependency table

| Stage | Depends on | Can be demoed standalone? |
|---|---|---|
| 1 | — | Yes (static graph view) |
| 2 | 1 | Yes (corridor overlay view) |
| 3 | 2 | Yes (distribution plots) |
| 4 | 1, 3 | **Yes — this is the minimum viable demo** |
| 5 | 4 | Only after 4 works |
| 6 | 4 (or 5) | Yes, once 4 works |
| 7 | 5, 6 | Only after 5 and 6 work |
| 8 | 6, 7 | Final integration |

This ordering matches the suggested build order in PRD 4 §5 — Stage 4 is the earliest point at which something demoable exists; Stage 5 is the most technically involved and safest to leave for last if time is short.

## 5. Acceptance criteria

- [ ] Every stage has exactly one primary technique/paper citation traceable to PRD 1.
- [ ] Every stage's "output" data structure matches the next stage's "input" — no undefined handoffs.
- [ ] The 8 stages here map 1:1 to the 5-step algorithm loop in PRD 2 §4.
