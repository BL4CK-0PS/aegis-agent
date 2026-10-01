"""
AEGIS Canonical Demo Scenario Specification
Defines configuration and initial telemetry envelopes for the GPS integrity degradation scenario.
"""

from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ScenarioDefinition(BaseModel):
    """
    Contract definition for the primary canonical incident demo scenario.
    """
    scenario_id: str = "SCN-GPS-INTEGRITY-001"
    name: str = "GPS Integrity Degradation & Autonomous Recovery"
    description: str = (
        "Canonical multi-stage incident demonstrating sensor discrepancy detection, "
        "evidence synthesis, competing hypotheses, operational mission impact, "
        "candidate action generation, counterfactual simulation, flight policy gating, "
        "operator authorization, authoritative execution, controlled verification failure, "
        "dynamic replanning, failsafe execution, and verified platform recovery."
    )
    initial_bias: float = 7.5
    seed: int = 42
    target_primary_action: str = "SWITCH_TO_IMU_ONLY"
    target_replacement_action: str = "ENTER_SAFE_MODE"
    expected_failure_metric: str = "navigation_confidence"


CANONICAL_SCENARIO = ScenarioDefinition()
