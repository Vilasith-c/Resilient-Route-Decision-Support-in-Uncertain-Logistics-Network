"""
engine_state.py — Inference Engine session state

Tracks the current evidence set, DBN time slice, and history of
ENGINE_RESULT snapshots across the demo session.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class EngineState:
    """
    Mutable state object persisted across evidence updates.

    Attributes
    ----------
    current_time_slice : int
        Which DBN time slice we're currently on (starts at 0).
    applied_evidence : dict
        Currently active evidence: {variable_name: state_value}.
    history : list[dict]
        List of past ENGINE_RESULT snapshots (for resilience metrics
        that need posterior time series).
    total_candidates_considered : int
        Running count of total route candidates generated before pruning
        (displayed in the UI as "pruned from N candidates").
    """
    current_time_slice: int = 0
    applied_evidence: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    total_candidates_considered: int = 0

    def apply_evidence(self, new_evidence: dict) -> None:
        """
        Merge new_evidence into applied_evidence and advance
        current_time_slice by 1 (Pipeline Stage 5 — DBN temporal step).
        """
        self.applied_evidence.update(new_evidence)
        self.current_time_slice += 1

    def step_forward(self) -> None:
        """
        Advance time slice without new evidence.
        Demonstrates that the DBN evolves belief even without fresh input.
        """
        self.current_time_slice += 1

    def reset(self) -> None:
        """Reset to a fresh state (for the "Reset demo" button)."""
        self.current_time_slice = 0
        self.applied_evidence.clear()
        self.history.clear()
        self.total_candidates_considered = 0

    def get_posteriors_history(self) -> list[dict]:
        """Extract just the posteriors from each historical ENGINE_RESULT."""
        return [
            result.get("posteriors", {})
            for result in self.history
            if "posteriors" in result
        ]
