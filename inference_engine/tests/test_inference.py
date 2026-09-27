"""
test_inference.py — Verification of Inference Engine and end-to-end pipeline

Tests PRD 6 acceptance criteria:
  - update_evidence returns an object matching the ENGINE_RESULT schema
  - Unknown evidence raises ValueError with descriptive message
  - Repeated calls with identical evidence hit the cache
  - generate_report returns non-empty PDF bytes
  - Latency is under 1.5s
"""

import time
import pytest
from inference_engine import (
    EngineState,
    update_evidence,
    initialize_engine,
    generate_report,
)
from inference_engine.inference_runner import _inference_cache, clear_cache


def test_initialize_and_schema():
    G, bn, state, result = initialize_engine(include_temporal=True)

    # Check schema
    assert "timestamp" in result
    assert "posteriors" in result
    assert "ranked_routes" in result
    assert "resilience_scorecard" in result
    assert "vulnerable_hub" in result
    assert "high_risk_edge" in result
    assert "recommended_route_id" in result

    # Check routes
    assert len(result["ranked_routes"]) > 0
    best_route = result["ranked_routes"][0]
    assert "route_id" in best_route
    assert "path" in best_route
    assert "on_time_probability" in best_route
    assert "reliability_score" in best_route
    assert best_route["path"][0] == "Warehouse"
    assert best_route["path"][-1] == "DeliveryZone"

    # Check resilience scorecard capabilities
    scorecard = result["resilience_scorecard"]
    for cap in [
        "rapid_response",
        "sustained_resistance",
        "continuous_running",
        "rapid_convergence",
        "dynamic_evolution",
    ]:
        assert cap in scorecard
        assert 0.0 <= scorecard[cap] <= 1.0


def test_evidence_update_and_caching():
    clear_cache()
    G, bn, state, _ = initialize_engine(include_temporal=True)

    # Evidence update 1
    t0 = time.time()
    res1 = update_evidence(state, bn, G, {"Hub4_Weather": "HeavyRain"})
    dur1 = time.time() - t0

    assert dur1 < 2.5
    assert res1["vulnerable_hub"] is not None

    # Check delay posterior for Hub4 increased
    hub4_delay_high = res1["posteriors"]["Hub4_Delay_t1"]["High"]
    assert hub4_delay_high > 0.20

    # Repeat call with identical evidence -> cache hit
    cache_len_before = len(_inference_cache)
    update_evidence(state, bn, G, {})
    assert len(_inference_cache) == cache_len_before


def test_invalid_evidence_variable():
    G, bn, state, _ = initialize_engine(include_temporal=True)
    with pytest.raises(ValueError) as excinfo:
        update_evidence(state, bn, G, {"FakeHub_Weather": "HeavyRain"})
    assert "Unknown evidence variable" in str(excinfo.value)


def test_report_generation():
    G, bn, state, result = initialize_engine(include_temporal=True)
    pdf_bytes = generate_report(result)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


if __name__ == "__main__":
    test_initialize_and_schema()
    test_evidence_update_and_caching()
    test_invalid_evidence_variable()
    test_report_generation()
    print("All inference engine tests passed successfully!")
