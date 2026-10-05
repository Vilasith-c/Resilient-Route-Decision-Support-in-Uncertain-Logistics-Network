"""
delay_distribution.py — Pipeline Stage 3: Skew-t Delay Distribution & Discretization
===================================================================================
Project: Interactive Tamil Nadu Resilient Logistics Simulator
Technique: Metro post-disruption skew-t / skew-normal model (PRD 1 §3.7, PRD 5 §5)

Academic Context (Con-Fix #2):
  - Chen et al. (2012) assumed symmetric Gaussian travel-time distributions.
  - Empirical post-disruption logistics data shows strong positive skew (heavy right
    tail): on-time shipments cluster near the lower bound, but disruptions produce
    prolonged, extreme right-tail delay cascades.
  - We fit a right-skewed distribution per corridor (using scipy.stats.skewnorm / jf_skew_t)
    and discretize into {Low, Medium, High} delay states by integrating the CDF at
    quantile thresholds [0.50, 0.80] for CPT initialization.

Assumption Log Note (PRD 8 §3 — Viva / Defense Transparency):
  - The skew-normal parameters (e.g. a=6.5, loc=18.0, scale=14.0 for coastal NH32;
    a=3.8 for NH44 Spine) are expert-elicited seeds (following the Wageningen
    methodology, PRD 1 §3.4), NOT empirically fitted from historical telematics logs,
    as no public post-disaster freight GPS telemetry dataset exists for this regional scope.
  - Specifying positive skew (a > 0) is a deliberate modeling requirement: it mathematically
    eliminates Chen et al.'s symmetric Gaussian limitation and encodes heavy-tailed delay risk.
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional
import numpy as np
from scipy import stats

from corridor_model import TAMIL_NADU_CORRIDORS


def fit_and_discretize_corridor(
    corridor_id: str,
    threshold_quantiles: Tuple[float, float] = (0.50, 0.80),
) -> Dict[str, float]:
    """
    Computes discrete CPT priors [P(Low), P(Medium), P(High)] for a corridor
    by evaluating the cumulative distribution function (CDF) of its right-skewed
    delay distribution.

    Parameters:
      corridor_id: key from TAMIL_NADU_CORRIDORS.
      threshold_quantiles: breakpoints (e.g. 50th and 80th percentiles).

    Returns:
      {"Low": p_low, "Medium": p_med, "High": p_high} summing to 1.0.
    """
    corridor_cfg = TAMIL_NADU_CORRIDORS.get(
        corridor_id,
        TAMIL_NADU_CORRIDORS["corridor_nh44_central_artery"]
    )
    p = corridor_cfg["skewnorm_params"]

    # Frozen skew-normal distribution with positive skew parameter a > 0
    dist = stats.skewnorm(a=p["a"], loc=p["loc"], scale=p["scale"])

    # Determine quantile delay cutoffs
    q_low_med = dist.ppf(threshold_quantiles[0])
    q_med_high = dist.ppf(threshold_quantiles[1])

    # Integrate CDF across the three state regions
    p_low = float(dist.cdf(q_low_med))
    p_med = float(dist.cdf(q_med_high) - p_low)
    p_high = float(1.0 - dist.cdf(q_med_high))

    # Numerical normalization guarantee
    total = p_low + p_med + p_high
    return {
        "Low": round(p_low / total, 4),
        "Medium": round(p_med / total, 4),
        "High": round(p_high / total, 4),
    }


def get_all_corridor_discretized_priors() -> Dict[str, Dict[str, float]]:
    """Generates the skew-t baseline CPT state probabilities for all 8 corridors."""
    return {
        cid: fit_and_discretize_corridor(cid)
        for cid in TAMIL_NADU_CORRIDORS.keys()
    }
