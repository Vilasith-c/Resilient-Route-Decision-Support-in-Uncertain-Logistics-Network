# PRD 2 — Idea Statement + Algorithm

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 1 (Paper Analysis)
**Status:** v1.0

---

## 1. Baseline retained (unchanged from original proposal)

- A logistics network of 20+ interconnected nodes: 1 warehouse (origin), 18 regional/sorting hubs, 1 delivery zone (destination), arranged as a directed graph.
- Each edge carries a base travel time and a base disruption probability.
- Evidence (e.g., "Heavy Rain = True", "Hub 8 Congestion = High") is fed into the network to update downstream probabilities.
- Posterior inference recomputes delay/on-time probability for every dependent variable.
- A derived Reliability Score per route combines on-time probability with disruption exposure.
- Output: a Probabilistic Logistics Resilience Report with a route comparison table, flagged vulnerable hub/edge, and a recommended route with plain-language justification.

**Nothing above changes.** Everything below replaces the *internals* of how each of these pieces is computed.

## 2. Combined problem statement

> Static, edge-independent, normally-distributed Bayesian route-reliability models (the project baseline, and Chen et al. 2012) produce a one-shot posterior over a snapshot network. They cannot (a) capture dependency between neighboring hubs sharing the same disruption source, (b) represent delay distributions that are empirically skewed and heavy-tailed rather than Gaussian, or (c) update belief continuously as new evidence streams in.

**Formal combined problem statement:**

> Design a path-centric, Dynamic Bayesian Network framework for resilient route decision support in a 20+ node logistics network, in which (i) disruption evidence propagates through both edge-level and correlated path-level uncertainty, (ii) delay distributions are modeled with heavy-tailed/skewed marginals rather than assumed Gaussian, (iii) beliefs are updated online as a two-time-slice DBN rather than recomputed from scratch, and (iv) the resulting per-route reliability scores are ranked using a provably-pruned α-reliable shortest path algorithm rather than brute-force enumeration — so the system outperforms naive shortest-path routing while remaining computationally tractable in real time.

## 3. Formal notation (extending Chen et al. 2012)

Let the logistics network be a directed graph **G = (N, E)** where:
- **N** = {warehouse, hub₁, …, hub₁₈, delivery-zone}, |N| ≥ 20
- **E** ⊆ N × N, each edge *e = (i, j)* carries a random travel time **T_ij**
- A **corridor** **C_k ⊆ E** is a set of edges sharing a common disruption source (adjacent hubs under the same weather cell, or all edges feeding a shared sorting hub)
- **α-reliable path definition (Chen et al. 2012):** given a travel-time budget *τ* and confidence level *α*, path *p* is α-reliable if P(T_p ≤ τ) ≥ α, where T_p is the path's total travel time
- **Path-centric extension (this project, after Andonov & Yang):** T_p for any path crossing a corridor C_k is drawn from a **joint corridor distribution** F_Ck, not the product of independent edge marginals
- **Skewed marginal (this project, after the metro paper):** each corridor's marginal delay distribution is modeled as **skew-t(ξ, ω, α, ν)** (location, scale, skew, degrees of freedom) rather than N(μ, σ²)
- **Time-indexed evidence (this project, after Jiang et al. and Hosseini & Ivanov):** every node/edge random variable X is represented at two time slices, X_t and X_(t+Δt), with X_(t+Δt) conditioned on both its parents at t+Δt and its own/parents' state at t

## 4. Master algorithm (pseudocode)

```
INPUT: Graph G, corridor definitions {C_k}, evidence stream Ev(t)
OUTPUT: Ranked route list with reliability scores, resilience report

1. BUILD_NETWORK(G)                         # PRD 3 Stage 1
2. FOR each corridor C_k in {C_k}:
     FIT skew-t(ξ,ω,α,ν) to historical/simulated delay samples   # Stage 3
     DISCRETIZE into {Low, Medium, High} delay states for CPTs
3. DEFINE_DBN(G, corridors)                  # Stage 2 + 4 + 5
     - slice t:   nodes = {WeatherState_t, HubCongestion_t, DelayState_t, ...}
     - slice t+Δt: same nodes, edges from t -> t+Δt (temporal) and
                    within t+Δt (causal, e.g. Weather -> Delay)
4. WHILE system is running:
     a. RECEIVE new evidence e (e.g. "Hub4.Congestion = High")
     b. RUN_INFERENCE(DBN, evidence=e)        # Stage 4/5 — forward inference
        -> posterior P(DelayState | evidence) for every hub/edge
     c. FOR each candidate route p in G:
          COMPUTE reliability_score(p) = f(on_time_prob(p), disruption_exposure(p))
     d. RANK routes using RSPP-A* with FSD dominance pruning   # Stage 6
        - discard dominated paths (Theorem: a sub-path of any
          non-dominated path is itself non-dominated — Chen et al. 2012)
     e. COMPUTE resilience_capabilities(G)     # Stage 7
        - rapid_response, sustained_resistance, continuous_running,
          rapid_convergence, dynamic_evolution   (Jiang et al.)
     f. IDENTIFY most vulnerable hub / highest-risk edge
     g. EMIT Probabilistic Logistics Resilience Report          # Stage 8
5. REPEAT step 4 on every new evidence event (online, not one-shot)
```

## 5. How each named con is solved (traceable to PRD 1)

| Con (paper, PRD 1 §) | Fix applied | Where in algorithm |
|---|---|---|
| Edge-independence assumption (Chen 2012, §3.1) | Path-centric corridor distributions (Andonov & Yang, §3.2) | Step 2–3 |
| Normal-distribution assumption (Chen 2012, §3.1) | Skew-t marginals (metro paper, §3.7) | Step 2 |
| Static BN / no temporal dynamics (Hosseini & Ivanov, §3.3) | Two-time-slice DBN (Jiang et al., §3.5) | Step 3–4 |
| Path-enumeration explosion (Mirchandani, cited in Chen 2012) | RSPP-LS/RSPP-A* dominance pruning (Chen 2012, §3.1) | Step 4d |
| One-time, non-continuous prediction (metro paper, §3.7) | Continuous DBN re-inference on each evidence event (Step 4, loop) | Step 4–5 |
| Untested on hub-and-spoke topology (RDBN airline, §3.6) | Our 20-node grid *is* a hub-and-spoke-style topology — validated by construction | Step 1 |
| Sub-optimal Baum-Welch CPT training (RDBN airline, §3.6) | CPTs calibrated from skew-t-derived discretization or expert elicitation (Wageningen, §3.4), not Baum-Welch | Step 2 |

## 6. Novelty statement

No single reviewed paper combines path-centric correlated uncertainty **and** skew-t marginals **and** two-time-slice dynamic updating **and** provably-pruned reliability ranking in one logistics-routing pipeline. Each individual piece is drawn from a cited, either-published-or-explicitly-flagged-as-technique-donor paper; the combination and its application to a concrete 20+ node logistics grid is this project's contribution.

## 7. Acceptance criteria

- [ ] Baseline PPT bullets (network modeling, uncertainty modeling, probabilistic propagation, dynamic belief updates, resilient recommendation) are all still present and traceable in §1.
- [ ] Every "fix" row in §5 cites a specific PRD 1 subsection.
- [ ] Pseudocode in §4 has a 1:1 mapping to the 8 pipeline stages defined in PRD 3.
