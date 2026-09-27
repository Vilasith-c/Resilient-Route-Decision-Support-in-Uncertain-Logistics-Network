"""
Inference Engine (PRD 6)
Middle layer: owns the current evidence state, orchestrates model layer calls,
produces ENGINE_RESULT for the frontend.

Public API (the ONLY three things PRD 7 code is allowed to import):
    from inference_engine import EngineState, update_evidence, generate_report
"""

import numpy as np

# NumPy 2.x backwards-compatibility shim for pgmpy 0.1.21
if not hasattr(np, "product"):
    np.product = np.prod

from .engine_state import EngineState
from .engine import update_evidence, initialize_engine
from .report_generator import generate_report

__all__ = ["EngineState", "update_evidence", "initialize_engine", "generate_report"]
