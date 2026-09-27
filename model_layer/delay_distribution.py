"""
delay_distribution.py — Pipeline Stage 3: Delay Distribution (skew-t)

Fits a skewed, heavy-tailed distribution per corridor and discretizes into
{Low, Medium, High} delay states for CPT construction.

Technique: Metro post-disruption skew-t model (PRD 1 §3.7).

Distribution choices (corrected from PRD 5 draft):
  - Primary:   scipy.stats.jf_skew_t  (Jones & Faddy skew-t)
                Produces genuinely skewed, heavy-tailed shapes matching
                empirical post-disruption delay behavior.
  - Fallback:  scipy.stats.skewnorm    (skew-normal)
                Lighter tails but still skewed; used if jf_skew_t fitting
                fails to converge on sparse data.
  - WRONG:     scipy.stats.nct         (non-central t — shifts mean, does
                NOT produce skew-t shape; explicitly excluded).

Critical rule:
    Never default to a symmetric distribution (skew=0).  If no historical
    data exists, seed with a plausible positive skew (a > 0) — a=0 silently
    reintroduces Chen 2012's original normal-distribution limitation.
"""

from __future__ import annotations
import numpy as np
from scipy import stats


# ---------------------------------------------------------------------------
# Default parameters for corridors with no historical data
# ---------------------------------------------------------------------------
# These are seeded to produce a right-skewed distribution (positive delays
# are more likely to be large than small — matching empirical disruption
# behavior from the metro paper).
DEFAULT_SKEWNORM_PARAMS = {
    "a": 4.0,       # positive skew (right tail heavier)
    "loc": 10.0,    # location: ~10 min baseline delay
    "scale": 8.0,   # spread
}

# For corridors with higher base risk, seed with heavier skew and larger scale.
HIGH_RISK_SKEWNORM_PARAMS = {
    "a": 6.0,
    "loc": 15.0,
    "scale": 12.0,
}


def fit_corridor_distribution(
    delay_samples: np.ndarray | None = None,
    high_risk: bool = False,
    use_jf_skew_t: bool = True,
) -> dict:
    """
    Fit a skewed distribution to delay samples for a single corridor.

    Parameters
    ----------
    delay_samples : np.ndarray or None
        Historical or simulated delay observations.  If None, uses
        expert-seeded defaults (Wageningen methodology, PRD 1 §3.4).
    high_risk : bool
        If True and no samples provided, uses higher-risk default params.
    use_jf_skew_t : bool
        If True, attempt Jones & Faddy skew-t fit first.  Falls back to
        skewnorm if jf_skew_t is unavailable or fit fails.

    Returns
    -------
    dict
        {"distribution": str, "params": dict} where params are the fitted
        distribution parameters.
    """
    if delay_samples is None or len(delay_samples) < 5:
        # Expert-seeded defaults — never symmetric
        defaults = HIGH_RISK_SKEWNORM_PARAMS if high_risk else DEFAULT_SKEWNORM_PARAMS
        return {
            "distribution": "skewnorm",
            "params": dict(defaults),
        }

    # Try Jones & Faddy skew-t first (genuine heavy tails)
    if use_jf_skew_t:
        try:
            jf_params = stats.jf_skew_t.fit(delay_samples)
            # jf_skew_t.fit returns (a, b, loc, scale)
            return {
                "distribution": "jf_skew_t",
                "params": {
                    "a": jf_params[0],
                    "b": jf_params[1],
                    "loc": jf_params[2],
                    "scale": jf_params[3],
                },
            }
        except (AttributeError, Exception):
            # jf_skew_t not available in this scipy version, or fit failed
            pass

    # Fallback: skew-normal
    a, loc, scale = stats.skewnorm.fit(delay_samples)
    if abs(a) < 0.01:
        # Guard: if fit converged to nearly symmetric, force positive skew
        a = 2.0  # mild right skew rather than reverting to Gaussian

    return {
        "distribution": "skewnorm",
        "params": {"a": a, "loc": loc, "scale": scale},
    }


def _get_scipy_dist(fit_result: dict):
    """Return a frozen scipy distribution from a fit result dict."""
    dist_name = fit_result["distribution"]
    params = fit_result["params"]

    if dist_name == "jf_skew_t":
        return stats.jf_skew_t(
            a=params["a"], b=params["b"],
            loc=params["loc"], scale=params["scale"],
        )
    elif dist_name == "skewnorm":
        return stats.skewnorm(
            a=params["a"], loc=params["loc"], scale=params["scale"],
        )
    else:
        raise ValueError(f"Unknown distribution: {dist_name}")


def discretize_to_cpt_states(
    fit_result: dict,
    thresholds: tuple[float, float] = (0.33, 0.66),
) -> dict[str, float]:
    """
    Convert a fitted distribution into P(Low), P(Medium), P(High) by
    integrating the CDF at the given quantile thresholds.

    Parameters
    ----------
    fit_result : dict
        Output of fit_corridor_distribution().
    thresholds : tuple[float, float]
        Quantile breakpoints separating Low/Medium and Medium/High.

    Returns
    -------
    dict[str, float]
        {"Low": p1, "Medium": p2, "High": p3} summing to 1.0.
    """
    dist = _get_scipy_dist(fit_result)

    q1 = dist.ppf(thresholds[0])
    q2 = dist.ppf(thresholds[1])

    p_low = dist.cdf(q1)
    p_med = dist.cdf(q2) - p_low
    p_high = 1.0 - dist.cdf(q2)

    # Numerical safety: ensure non-negative and sums to 1
    probs = {"Low": max(p_low, 0.0), "Medium": max(p_med, 0.0), "High": max(p_high, 0.0)}
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}

    return probs


def generate_synthetic_delay_samples(
    n_samples: int = 200,
    base_travel_time: float = 20.0,
    disruption_prob: float = 0.1,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Generate synthetic delay samples for a corridor, simulating the
    mixture of normal operations and disruption events.

    This is used when no real historical data exists (college project
    context) but we want to demonstrate the fitting pipeline with
    genuinely skewed data rather than hardcoded CPTs.

    Parameters
    ----------
    n_samples : int
        Number of samples to generate.
    base_travel_time : float
        Baseline travel time (minutes).
    disruption_prob : float
        Probability that any given trip encounters a disruption.
    rng : np.random.Generator or None
        Random number generator for reproducibility.

    Returns
    -------
    np.ndarray
        Array of delay values (minutes above baseline).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    delays = np.zeros(n_samples)
    for i in range(n_samples):
        if rng.random() < disruption_prob:
            # Disrupted: heavy-tailed delay (exponential + baseline)
            delays[i] = rng.exponential(scale=base_travel_time * 0.5) + base_travel_time * 0.2
        else:
            # Normal: small random variation
            delays[i] = max(0, rng.normal(loc=2.0, scale=1.5))

    return delays
