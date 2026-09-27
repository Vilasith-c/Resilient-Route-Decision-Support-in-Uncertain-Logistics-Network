"""
inference_runner.py — Pipeline Stages 4 & 5 inference wrapper

This is the ONLY module allowed to import pgmpy.inference.
Wraps VariableElimination for the duplicated-node BN approach.

Caching strategy:
    Manual dict keyed on frozenset(evidence.items()) + time_slice,
    because functools.lru_cache cannot handle dict arguments (dicts
    aren't hashable).
"""

from __future__ import annotations
from pgmpy.inference import VariableElimination
from pgmpy.models import BayesianNetwork


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
_inference_cache: dict[tuple, dict] = {}


def clear_cache() -> None:
    """Clear the inference result cache."""
    _inference_cache.clear()


def _cache_key(evidence: dict, time_slice: int) -> tuple:
    """Build a hashable cache key from evidence dict and time slice."""
    return (frozenset(sorted(evidence.items())), time_slice)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_evidence(bn: BayesianNetwork, evidence: dict) -> None:
    """
    Validate that all evidence variable names exist in the BN.

    Raises ValueError with a descriptive message listing unknown variable
    names, rather than letting pgmpy fail silently or throw an opaque
    internal exception.
    """
    valid_names = set(bn.nodes())
    unknown = set(evidence.keys()) - valid_names
    if unknown:
        raise ValueError(
            f"Unknown evidence variable(s): {unknown}. "
            f"Valid variables include: {sorted(list(valid_names))[:10]}..."
        )


def _validate_evidence_states(bn: BayesianNetwork, evidence: dict) -> None:
    """
    Validate that evidence state values are valid for their respective nodes.
    """
    for var, state in evidence.items():
        cpd = bn.get_cpds(var)
        if cpd is not None:
            valid_states = cpd.state_names.get(var, [])
            if valid_states and state not in valid_states:
                raise ValueError(
                    f"Invalid state '{state}' for variable '{var}'. "
                    f"Valid states: {valid_states}"
                )


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def run_inference(
    bn: BayesianNetwork,
    evidence: dict,
    time_slice: int = 0,
) -> dict[str, dict[str, float]]:
    """
    Run exact inference over the BN given evidence.

    Uses VariableElimination on the plain BayesianNetwork with duplicated
    _t0/_t1 nodes (NOT DBNInference on a DynamicBayesianNetwork).

    Parameters
    ----------
    bn : BayesianNetwork
        The two-time-slice BN from dbn_model.build_bn().
    evidence : dict
        {variable_name: state_value}, e.g. {"Hub4_Weather_t0": "HeavyRain"}.
    time_slice : int
        Which time slice to query (0 or 1).

    Returns
    -------
    dict[str, dict[str, float]]
        {node_name: {"Low": p, "Medium": p, "High": p}, ...}
        for all delay nodes in the requested time slice.
    """
    # Check cache
    key = _cache_key(evidence, time_slice)
    if key in _inference_cache:
        return _inference_cache[key]

    # Validate evidence
    validate_evidence(bn, evidence)
    _validate_evidence_states(bn, evidence)

    # Run inference
    infer = VariableElimination(bn)
    suffix = f"_t{time_slice}"

    # Query all delay nodes in this time slice
    delay_nodes = [n for n in bn.nodes() if "_Delay" in n and n.endswith(suffix)]

    result: dict[str, dict[str, float]] = {}

    for node in delay_nodes:
        try:
            query_result = infer.query(
                variables=[node],
                evidence=evidence,
                show_progress=False,
            )
            # Extract probabilities
            state_names = query_result.state_names.get(node, [])
            values = query_result.values
            result[node] = {
                state: round(float(prob), 6)
                for state, prob in zip(state_names, values)
            }
        except Exception as e:
            # If inference fails for a specific node, use uniform prior
            result[node] = {"Low": 0.33, "Medium": 0.34, "High": 0.33}

    # Also query weather and congestion nodes for display
    cause_nodes = [
        n for n in bn.nodes()
        if ("_Weather" in n or "_Congestion" in n) and n.endswith(suffix)
        and n not in evidence  # don't query observed nodes
    ]

    for node in cause_nodes:
        try:
            query_result = infer.query(
                variables=[node],
                evidence=evidence,
                show_progress=False,
            )
            state_names = query_result.state_names.get(node, [])
            values = query_result.values
            result[node] = {
                state: round(float(prob), 6)
                for state, prob in zip(state_names, values)
            }
        except Exception:
            pass

    # Cache result
    _inference_cache[key] = result
    return result
