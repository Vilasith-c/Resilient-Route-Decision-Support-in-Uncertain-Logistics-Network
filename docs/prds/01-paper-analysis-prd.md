# PRD 1 — Paper Analysis

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Document owner:** Team (Bhanu Vilasith Reddy Chilka, Elluru Ritesh Goud, Prem Santh C K)
**Course:** 22AIE301 — Probabilistic Reasoning, Amrita Vishwa Vidyapeetham
**Status:** v1.0

---

## 1. Purpose

This document is the literature foundation for the project. It records, for every paper the team has reviewed, its publication status, methodology, core algorithm, the limitations the authors themselves admit, and the exact reason that paper was pulled into this project. Every claim made in PRDs 2–7 traces back to a row in the table below — no technique is used without a citation, and no citation is used without its stated limitation being addressed somewhere downstream.

## 2. Publication-status policy

Per project convention, **published, peer-reviewed papers are the primary/high-impact anchors**; **arXiv-only preprints are used only as technique donors**, never as the sole justification for a design decision.

| Tier | Meaning |
|---|---|
| **Anchor (published)** | Peer-reviewed journal or accepted-in-journal paper. Cite as primary evidence. |
| **Anchor (published, conference)** | Peer-reviewed conference proceedings. Cite as primary evidence. |
| **Technique donor (archived/preprint)** | arXiv-only or technical report. Cite only for the specific algorithm/technique borrowed, with an explicit note that the parent claim is corroborated by an anchor paper wherever possible. |

## 3. Paper-by-paper analysis

### 3.1 Chen, Lam, Sumalee, Li, Shao, Fang (2012)
**"Finding Reliable Shortest Paths in Road Networks Under Uncertainty"** — *Networks and Spatial Economics*, Springer. **[ANCHOR — published journal]**

- **Problem addressed:** Determine the α-reliable shortest path — the path minimizing the travel-time budget required to guarantee a pre-specified on-time arrival probability — in a road network with stochastic, normally-distributed link travel times.
- **Core method:** Multi-criteria shortest-path formulation. Establishes dominance conditions under first-order stochastic dominance (FSD) so that dominated (provably worse) paths can be discarded during search without full enumeration.
- **Algorithms proposed:** RSPP-LS (multi-criteria label-setting) and RSPP-A* (multi-criteria A*, using a destination-directed heuristic to reduce search space). RSPP-A* is reported to cut computation time 20–50% versus RSPP-LS.
- **Validation:** Six large-scale road networks plus a real-world case study using Hong Kong's Real-time Traveller Information System (RTIS).
- **Authors' own stated limitations:**
  1. Link travel times are assumed to follow a **normal distribution** — may not hold in reality.
  2. **Correlation between neighboring links is omitted for simplicity**, despite the authors citing empirical evidence that travel times are strongly correlated among neighboring links.
  3. Link travel times are assumed **stable over a fixed period** (e.g., one peak-hour window) — not time-of-day varying.
- **Relevance to this project:** This is the formal mathematical backbone for our route-reliability ranking stage (Pipeline Stage 6). The three limitations above are exactly the three gaps this project closes using the other six papers.

### 3.2 Andonov & Yang — SPOTAR / PACE model
**"A New Formulation of the Shortest Path Problem with On-Time Arrival Reliability"** — arXiv technical report, extending a paper accepted at **IEEE MDM 2018** (published conference). **[TECHNIQUE DONOR — cite the IEEE MDM 2018 paper as the anchor where possible; the arXiv document is an extension report with additional experiments]**

- **Problem addressed:** The SPOTAR problem — given a source, destination, and time budget, find the path maximizing on-time arrival probability — solved under the **PACE (PAth-CEntric)** uncertain road network model, where uncertain travel times attach to whole *paths*, not just individual edges.
- **Core method:** A generic search algorithm with speed-up heuristics that exploits path-level (not just edge-level) travel-time distributions, validated on real GPS trajectory data.
- **Key contribution for us:** Directly solves Chen et al.'s (2012) limitation #2 (ignored link correlation) by modeling dependency at the path/corridor level instead of assuming edge independence.
- **Authors' own stated limitation:** Future work explicitly calls for further speed-up strategies (contraction hierarchies, hub labeling, parallel computing) to scale to larger networks — the current algorithm is not yet optimized for very large graphs.

### 3.3 Hosseini & Ivanov (2020)
**"Bayesian Networks for Supply Chain Risk, Resilience and Ripple Effect Analysis: A Literature Review"** — Accepted in *Expert Systems with Applications*. **[ANCHOR — published journal]**

- **Problem addressed:** Systematic review (network analysis, scientometric analysis, clustering) of peer-reviewed BN applications to supply-chain risk and resilience, 2007–2019.
- **Core contribution for us:** A rigorous statement of BN's strengths (forward/backward inference, works with small/incomplete data, combines expert knowledge with data, handles mixed variable types, explicit uncertainty encoding) and its **three theoretical limitations**:
  1. **Lack of feedback loops** — BNs are acyclic (DAGs), so closed-loop/cyclic systems cannot be represented directly.
  2. **Poor temporal dynamics** — a static BN cannot represent variables that change over time; the paper explicitly recommends **Dynamic Bayesian Networks (DBN)** as the fix.
  3. **Prior-knowledge sensitivity** — results are only as good as the reliability of the prior/expert-elicited probabilities.
- **Relevance to this project:** This is our theoretical justification for using a BN at all, and the paper's own recommended fix (DBN) is exactly what we implement in Pipeline Stage 5.

### 3.4 Wageningen University (ICAE 2018)
**"A Bayesian Network as a Tool to Measure Supply Chain Resilience"** — Conference paper, International Conference of Agricultural Economists 2018. **[ANCHOR — published conference proceedings]**

- **Problem addressed:** Build a quantitative "Diagnostic Tool" linking resilience attributes (engineering, agility, collaboration, risk-management thinking) to profitability stability, applied to a Dutch pork supply chain.
- **Core method:** Bayesian Belief Network with expert-elicited conditional probability tables (CPTs).
- **Relevance to this project:** Methodological precedent for building CPTs from expert judgement when historical disruption data is scarce — directly applicable to our "Reliability Score" derivation where real disruption logs for a college project are limited.
- **Implicit limitation:** Relies entirely on expert-elicited CPTs, which the paper's own discussion flags as needing further validation against real disruption data (the fipronil poultry case is proposed as the next validation target).

### 3.5 Jiang, Yang, Cheng, Gao, Feng, Zhou
**"A Quantitative Framework for Network Resilience Evaluation using Dynamic Bayesian Network"** — arXiv. **[TECHNIQUE DONOR — archived]**

- **Problem addressed:** Quantify time-varying resilience of computer/communication networks under attack and recovery, using a two-time-slice DBN.
- **Core method:** Defines five core resilience capabilities — *rapid response, sustained resistance, continuous running, rapid convergence, dynamic evolution* — each quantified via DBN inference across a two-time-slice structure (time *t* and *t+Δt*).
- **Key contribution for us:** The exact DBN mechanics (two-time-slice conditional dependency) used in Pipeline Stage 5, and the five-capability resilience taxonomy used in Pipeline Stage 7.
- **Authors' own stated limitation:** The framework is validated only in the computer-network/cybersecurity domain; the authors' own future work explicitly proposes extending it to a "physical network environment" — which is precisely what this project does by applying it to a logistics network.

### 3.6 Relational Dynamic Bayesian Network for Airline Disruption Management
arXiv preprint. **[TECHNIQUE DONOR — archived]**

- **Problem addressed:** Uncertainty quantification and propagation through the phases of a flight schedule (proactive/reactive/post-execution) using a Relational DBN (RDBN) built from chained Hidden Markov Models per flight phase.
- **Authors' own stated limitations:**
  1. Validated only on a **point-to-point** airline route network — explicitly flagged as untested on **hub-and-spoke** topology.
  2. The Baum-Welch algorithm used to train the component HMMs is called out by the authors themselves as **"inherently sub-optimal."**
- **Relevance to this project:** Our 20+ node hub-and-spoke-style grid is exactly the topology this paper couldn't test — a natural extension point worth stating explicitly in our report. We deliberately avoid inheriting their Baum-Welch weakness (see PRD 5, §CPT calibration).

### 3.7 Metro Post-Disruption Travel Time Prediction
**"A Bayesian Framework for Post-disruption Travel Time Prediction in Metro Networks"** — arXiv preprint (2026). **[TECHNIQUE DONOR — archived, most recent]**

- **Problem addressed:** Predict post-disruption train travel times using a Bayesian spatiotemporal model with **skew-t distributed error terms** instead of a normal-distribution assumption, validated on Montréal metro data.
- **Core finding:** Post-disruption travel times are empirically **heteroskedastic, skewed, and heavy-tailed** — normal-distribution baselines are consistently outperformed.
- **Key contribution for us:** Direct fix for Chen et al.'s (2012) limitation #1 (normal-distribution assumption).
- **Authors' own stated limitation:** The model gives only a **one-time prediction** at the moment a disruption is reported resolved; the authors explicitly name "extend to an online forecasting setting, in which predictions are continuously updated" as future work.
- **Relevance to this project:** Our DBN-based continuous belief update (Pipeline Stage 5) is a direct implementation of the exact extension this paper's authors call for but did not build.

## 4. Summary matrix

| # | Paper | Status | Primary technique used | Con(s) fixed by this project |
|---|---|---|---|---|
| 1 | Chen et al. 2012 | Anchor (journal) | RSPP-LS / RSPP-A*, α-reliable path formalism | Fixed by papers 2, 7 (correlation, distribution) |
| 2 | Andonov & Yang (SPOTAR/PACE) | Technique donor | Path-centric dependency modeling | Fixes Chen 2012's con #2 |
| 3 | Hosseini & Ivanov | Anchor (journal) | BN forward/backward inference theory | Its own con #2 fixed by paper 5 (DBN) |
| 4 | Wageningen ICAE 2018 | Anchor (conference) | Expert-elicited CPT methodology | Supplements paper 6's CPT weakness |
| 5 | Jiang et al. (DBN resilience) | Technique donor | Two-time-slice DBN, 5 resilience capabilities | Fixes Hosseini & Ivanov's con #2 |
| 6 | RDBN Airline Disruption | Technique donor | Phase-chained HMM/RDBN concept | Its Baum-Welch weakness avoided (PRD 5) |
| 7 | Metro skew-t paper | Technique donor | Skew-t heavy-tailed delay distribution | Fixes Chen 2012's con #1; its own "one-time prediction" con fixed by paper 5's DBN |

## 5. Reading queue for future depth (papers-of-papers)

- Chen et al. (2012b) — the authors' own extension incorporating correlated link travel times.
- Chen et al. (2012c) — the authors' own extension to time-dependent networks.
- Yang, Dai, Guo, Jensen, Hu — "PACE: a PAth-CEntric paradigm for stochastic path finding," *VLDB Journal* 27(2), 2018 — full peer-reviewed version behind SPOTAR.
- Hosseini & Ivanov (2019) — earlier paper testing BN-based disruption propagation directly.
- Yodo — original DBN-for-engineered-resilient-systems paper cited inside Jiang et al.

## 6. Acceptance criteria for this PRD

- [ ] Every technique cited in PRDs 2–7 has a corresponding row in §3 of this document.
- [ ] Every "con fixed" claim in PRD 2 references the exact limitation quoted here, not a paraphrase.
- [ ] No arXiv-only paper is cited as the sole justification for a core design decision without an anchor paper alongside it.
