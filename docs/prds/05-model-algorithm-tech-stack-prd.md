# PRD 5 — Model and Algorithm (Tech Stack)

**Project:** A Bayesian Network Framework for Resilient Route Decision Support in Uncertain Logistics Networks
**Depends on:** PRD 2 (Idea Statement + Algorithm), PRD 3 (Pipeline), PRD 4 (Technical Application Pipeline)
**Consumed by:** PRD 6 (Inference Engine)
**Status:** v1.0

---

## 1. Purpose

This is the lowest layer of the application — pure model definition and algorithms, with no notion of "the current evidence" or any UI. Everything here should be unit-testable by calling functions directly in a Python shell with no Streamlit process running.

## 2. Tech stack for this layer

| Component | Library | Version guidance |
|---|---|---|
| Graph structure | `networkx` | ≥ 3.0 |
| Bayesian/Dynamic Bayesian Network | `pgmpy` | ≥ 0.1.24 (has `DynamicBayesianNetwork` class) |
| Skewed distribution fitting | `scipy.stats.skewnorm` (skew-normal approximation) or `scipy.stats.nct` (true skew-t via non-central t) | scipy ≥ 1.10 |
| Numerical/array support | `numpy`, `pandas` | latest stable |

## 3. Module: `graph_builder.py` (Pipeline Stage 1)

**Responsibility:** Build the 20+ node directed graph with base attributes.

```python
import networkx as nx

def build_logistics_graph() -> nx.DiGraph:
    """
    Returns a DiGraph with nodes: 'Warehouse', 'Hub1'..'Hub18', 'DeliveryZone'.
    Each edge carries:
      - base_travel_time: float (minutes)
      - base_disruption_prob: float in [0,1]
    """
    G = nx.DiGraph()
    # ... add_node / add_edge calls per the 6x3 grid layout from the baseline PPT
    return G
```

**Node attribute schema:**

```python
{
    "node_type": "warehouse" | "hub" | "delivery_zone",
    "risk_level": "normal" | "high_congestion" | "high_risk"   # from baseline legend
}
```

**Edge attribute schema:**

```python
{
    "base_travel_time": float,        # minutes
    "base_disruption_prob": float,    # 0..1
    "corridor_id": str | None         # set in Stage 2, null until then
}
```

## 4. Module: `corridor_model.py` (Pipeline Stage 2 — path-centric dependency)

**Responsibility:** Group edges that plausibly share a disruption source into corridors (fixes Chen et al. 2012's independence assumption, per PACE/SPOTAR, PRD 1 §3.2).

```python
def define_corridors(G: nx.DiGraph) -> dict[str, list[tuple]]:
    """
    Returns {corridor_id: [edge, edge, ...]}.
    Grouping heuristic for the 6x3 grid (lightweight PACE approximation):
      - all horizontal edges in the same grid row -> one corridor
        (shared weather-cell exposure)
      - all edges feeding into the same downstream hub -> one corridor
        (shared congestion-source exposure)
    """
    ...

def assign_corridor_ids(G: nx.DiGraph, corridors: dict) -> None:
    """Mutates G in place, setting edge['corridor_id'] for every edge."""
    ...
```

## 5. Module: `delay_distribution.py` (Pipeline Stage 3 — skew-t discretization)

**Responsibility:** Fit a skewed distribution per corridor and discretize into {Low, Medium, High} states for CPT construction (fixes Chen et al. 2012's normal-distribution assumption, per the metro paper, PRD 1 §3.7).

```python
from scipy import stats
import numpy as np

def fit_corridor_distribution(delay_samples: np.ndarray) -> dict:
    """
    Fits scipy.stats.skewnorm (or nct for true skew-t) to delay_samples.
    Returns fitted parameters: {"loc": ..., "scale": ..., "skew": ...}
    If no historical data exists, seed with a plausible skew (a > 0) rather
    than defaulting to a=0 (normal) — a=0 silently reintroduces Chen 2012's
    original limitation.
    """
    a, loc, scale = stats.skewnorm.fit(delay_samples)
    return {"a": a, "loc": loc, "scale": scale}

def discretize_to_cpt_states(params: dict, thresholds=(0.33, 0.66)) -> dict:
    """
    Converts a fitted skewnorm distribution into P(Low), P(Medium), P(High)
    by integrating the CDF at the given quantile thresholds.
    Returns {"Low": p1, "Medium": p2, "High": p3} summing to 1.0.
    """
    dist = stats.skewnorm(params["a"], loc=params["loc"], scale=params["scale"])
    q1 = dist.ppf(thresholds[0])
    q2 = dist.ppf(thresholds[1])
    p_low = dist.cdf(q1)
    p_med = dist.cdf(q2) - p_low
    p_high = 1 - dist.cdf(q2)
    return {"Low": p_low, "Medium": p_med, "High": p_high}
```

**Why discretize instead of keeping it continuous:** `pgmpy`'s standard `DiscreteBayesianNetwork`/`DynamicBayesianNetwork` classes expect categorical CPTs, which also matches the baseline PPT's own evidence format ("Hub 8 Congestion = High"). The underlying generative model is still genuinely skewed/heavy-tailed — only the CPT *inputs* are discretized, not the modeling assumption.

## 6. Module: `dbn_model.py` (Pipeline Stages 4 & 5 — BN structure + DBN temporal layer)

**Responsibility:** Define the discrete BN structure and its two-time-slice DBN extension.

```python
from pgmpy.models import DynamicBayesianNetwork as DBN
from pgmpy.factors.discrete import TabularCPD

def build_dbn(corridors: dict, cpt_seeds: dict) -> DBN:
    """
    Builds a two-time-slice DBN.
    Node naming convention: (variable_name, time_slice) e.g. ('Hub4_Weather', 0).

    Intra-slice edges (causal, within one time slice), e.g.:
        ('Hub4_Weather', 0) -> ('Hub4_Delay', 0)
    Inter-slice edges (temporal, Jiang et al. two-time-slice mechanism):
        ('Hub4_Delay', 0) -> ('Hub4_Delay', 1)
        ('Hub4_Weather', 0) -> ('Hub4_Weather', 1)

    CPTs for each node are seeded from delay_distribution.discretize_to_cpt_states()
    where the node represents a corridor's delay state, and from expert-elicited
    values (Wageningen methodology, PRD 1 §3.4) where the node represents a
    weather/congestion cause variable with no historical samples available.
    """
    dbn = DBN()
    # dbn.add_edges_from([...])
    # dbn.add_cpds(...)
    dbn.initialize_initial_state()
    return dbn
```

**Note on avoiding the RDBN airline paper's flagged weakness (PRD 1 §3.6):** do **not** train CPTs with a raw Baum-Welch/EM pass on sparse simulated data — the source paper's own authors call this "inherently sub-optimal." Prefer CPTs seeded from the skew-t discretization (§5) or expert elicitation (Wageningen methodology), optionally refined with a small number of EM iterations only where real historical samples exist.

## 7. Module: `reliability_ranking.py` (Pipeline Stage 6 — RSPP-LS / RSPP-A*)

**Responsibility:** Implement Chen et al.'s (2012) label-setting and A* algorithms with FSD dominance pruning — this is the project's hand-written algorithmic contribution (not available in `networkx` or `pgmpy`).

```python
from dataclasses import dataclass

@dataclass
class Label:
    node: str
    cumulative_time_budget: float
    on_time_probability: float
    path: list[str]

def dominates(label_a: Label, label_b: Label) -> bool:
    """
    First-order stochastic dominance (FSD) check per Chen et al. 2012.
    label_a dominates label_b if label_a reaches the same node with a
    time budget <= label_b's AND on_time_probability >= label_b's,
    with at least one strict inequality.
    """
    ...

def rspp_ls(G, source: str, target: str, time_budget: float) -> list[Label]:
    """
    Multi-criteria label-setting algorithm (RSPP-LS).
    Maintains a set of non-dominated labels at every node; discards any
    label that is dominated per `dominates()` above (Theorem 1, Chen et
    al. 2012: a sub-path of a non-dominated path is itself non-dominated).
    Returns the set of non-dominated labels reaching `target`.
    """
    ...

def rspp_astar(G, source: str, target: str, time_budget: float, heuristic) -> list[Label]:
    """
    RSPP-A* — same dominance logic as rspp_ls, but prioritizes expansion
    of labels closer to `target` using `heuristic` (e.g. remaining
    Euclidean/grid distance). Chen et al. report 20-50% speedup over
    RSPP-LS on large networks.
    """
    ...
```

**Complexity note:** Naive path enumeration is exponential (Mirchandani's original algorithm, cited as unusable at scale in Chen et al. 2012). RSPP-LS/A* avoid this by discarding dominated labels at each node during search rather than generating every path — the 20-node grid is small enough that either variant will run in well under a second, but implementing the pruning is still the point: it demonstrates the actual algorithmic contribution rather than a brute-force stand-in.

## 8. Module: `resilience_metrics.py` (Pipeline Stage 7)

**Responsibility:** Compute the five DBN resilience capabilities (Jiang et al., PRD 1 §3.5), adapted from the computer-network domain to the physical logistics domain.

```python
def compute_resilience_scorecard(dbn_posteriors_over_time: list[dict]) -> dict:
    """
    Given a sequence of posterior snapshots across time slices, computes:
      - rapid_response: how quickly delay-state probabilities react to new evidence
      - sustained_resistance: how much on-time probability degrades under sustained disruption
      - continuous_running: fraction of routes remaining non-dominated throughout
      - rapid_convergence: how quickly posteriors return to baseline after disruption clears
      - dynamic_evolution: overall trend of network reliability across time slices
    Returns a dict of five floats in [0,1].
    """
    ...

def identify_vulnerable_hub(G, posteriors: dict) -> str:
    """Returns the node with highest weighted contribution to route delay risk."""
    ...

def identify_high_risk_edge(G, posteriors: dict) -> tuple:
    """Returns the edge with highest weighted contribution to route delay risk."""
    ...
```

## 9. File/module structure

```
model_layer/
  __init__.py
  graph_builder.py        # Stage 1
  corridor_model.py       # Stage 2
  delay_distribution.py   # Stage 3
  dbn_model.py            # Stages 4-5
  reliability_ranking.py  # Stage 6
  resilience_metrics.py   # Stage 7
  tests/
    test_graph_builder.py
    test_corridor_model.py
    test_delay_distribution.py
    test_dbn_model.py
    test_reliability_ranking.py
    test_resilience_metrics.py
```

## 10. Acceptance criteria

- [ ] Every function in this layer is callable and testable with no Streamlit/UI process running.
- [ ] `discretize_to_cpt_states` never silently defaults to a symmetric (non-skewed) distribution when historical data is missing.
- [ ] `rspp_ls`/`rspp_astar` correctly discard dominated labels (verified with a small hand-checkable test graph).
- [ ] CPT calibration never relies solely on raw Baum-Welch/EM per §6's note.
