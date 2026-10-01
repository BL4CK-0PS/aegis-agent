"""
AEGIS State Tools
Implements get_system_state, get_observations, and get_trust.
"""

from __future__ import annotations
from typing import Any, Dict
from app.core.models import Observations
from app.core.trust import TrustEngine
from app.tools.context import ToolContext
from app.tools.registry import Tool


class GetSystemStateTool(Tool):
    name = "get_system_state"
    description = (
        "Retrieves current system telemetry, vehicle position, velocity, navigation mode, "
        "energy reserve, and mission status."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "time": {"type": "number"},
            "position": {"type": "object"},
            "velocity": {"type": "object"},
            "navigation_mode": {"type": "string"},
            "gps_trust": {"type": "number"},
            "imu_trust": {"type": "number"},
            "mission_progress": {"type": "number"},
            "mission_status": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        return state.model_dump()


class GetObservationsTool(Tool):
    name = "get_observations"
    description = (
        "Retrieves raw and filtered sensor observations, comparing GPS solution against "
        "inertial dead-reckoning trajectory to calculate positional residual and anomaly metrics."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "gps_position": {"type": "object"},
            "predicted_position": {"type": "object"},
            "residual": {"type": "number"},
            "anomaly_score": {"type": "number"},
            "provenance": {"type": "array", "items": {"type": "string"}},
            "timestamp": {"type": "number"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        obs = Observations(
            gps_position=state.gps_position or state.position,
            predicted_position=state.predicted_position or state.position,
            residual=state.residual,
            anomaly_score=state.anomaly_score,
            provenance=["simulator:gps_receiver", "simulator:inertial_dead_reckoning"],
            timestamp=state.time,
            description=(
                f"Position residual: {state.residual:.2f}m. Anomaly score: {state.anomaly_score:.3f}. "
                f"GPS fault flag: {state.gps_fault_active}."
            ),
        )
        return obs.model_dump()


class GetTrustTool(Tool):
    name = "get_trust"
    description = (
        "Calculates dynamic integrity trust scores for GPS, IMU, and communication links, "
        "providing causal explanations for any observed confidence degradation."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "gps_trust": {"type": "number"},
            "imu_trust": {"type": "number"},
            "communication_trust": {"type": "number"},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "timestamp": {"type": "number"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        snapshot = TrustEngine.evaluate(state)
        return snapshot.model_dump()
