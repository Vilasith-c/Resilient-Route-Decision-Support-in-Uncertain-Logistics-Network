"""
Model & Algorithm Layer (PRD 5)
Pure model definition and algorithms — no UI, no session state.
Every function here is unit-testable from a Python shell.
"""

import numpy as np

# NumPy 2.x backwards-compatibility shim for pgmpy 0.1.21
if not hasattr(np, "product"):
    np.product = np.prod
