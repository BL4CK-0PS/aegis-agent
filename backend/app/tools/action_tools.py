"""
AEGIS Action & Governance Tools
Implements generate_actions, simulate_action, evaluate_policy,
execute_action, verify_action, and replan.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.models import (
    CandidateAction,
    NavigationMode,
    PolicyEvaluation,
    PolicyStatus,
    SimulationResult,
    SystemState,
)
from app.tools.context import ToolContext
from app.tools.registry import Tool


class GenerateActionsTool(Tool):
    name = "generate_actions"
    description = (
        "Generates candidate operational response actions tailored to the current "
        "system state and degradation level."
    )
    input_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "risk": {"type": "number"},
                        "mission_continuity": {"type": "number"},
                    },
                },
            },
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        actions = [
            CandidateAction(
                id="continue_gps",
                name="Continue GPS-assisted Navigation",
                risk=0.88 if state.gps_fault_active else 0.05,
                mission_continuity=0.95 if not state.gps_fault_active else 0.35,
                description="Maintain current GPS tracking without sensor reconfiguration.",
                target_mode=NavigationMode.GPS_ASSISTED,
            ),
            CandidateAction(
                id="switch_inertial",
                name="Switch to Inertial Navigation",
                risk=0.42,
                mission_continuity=0.71,
                description="Isolate corrupted GPS signal and engage IMU dead-reckoning filter.",
                target_mode=NavigationMode.INERTIAL,
            ),
            CandidateAction(
                id="safe_mode",
                name="Enter Safe Mode",
                risk=0.08,
                mission_continuity=0.00,
                description="Arrest forward velocity into stationary hover / controlled emergency descent.",
                target_mode=NavigationMode.SAFE_MODE,
            ),
        ]
        return {"actions": [a.model_dump() for a in actions]}


class SimulateActionTool(Tool):
    name = "simulate_action"
    description = (
        "Executes a deterministic counterfactual simulation of a candidate action, "
        "forecasting predicted risk, mission continuity, and recovery duration prior to execution."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action to simulate: continue_gps, switch_inertial, or safe_mode.",
            },
            "action_id": {
                "type": "string",
                "description": "Alternative key for action identifier.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string"},
            "predicted_mission_outcome": {"type": "string"},
            "predicted_risk": {"type": "number"},
            "energy_impact": {"type": "number"},
            "residual_uncertainty": {"type": "number"},
            "expected_recovery_time": {"type": "number"},
            "mission_continuity": {"type": "number"},
            "recommendation": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        norm = action_id.lower().strip()
        state = context.simulator.get_state()

        if norm in ("continue_gps", "continue_gps_assisted"):
            sim = SimulationResult(
                action_id="continue_gps",
                action_name="Continue GPS-assisted Navigation",
                predicted_mission_outcome="Trajectory divergence leading to catastrophic geofence departure within 15s.",
                predicted_risk=0.92,
                energy_impact=-1.5,
                residual_uncertainty=8.5,
                expected_recovery_time=0.0,
                mission_continuity=0.35,
                recommendation="REJECTED: Exceeds safe operational envelope. High collision risk.",
            )
        elif norm in ("switch_inertial", "switch_to_inertial"):
            sim = SimulationResult(
                action_id="switch_inertial",
                action_name="Switch to Inertial Navigation",
                predicted_mission_outcome="Decouples corrupt GPS; preserves route progress with dead-reckoning drift.",
                predicted_risk=0.42,
                energy_impact=-0.8,
                residual_uncertainty=2.2,
                expected_recovery_time=12.0,
                mission_continuity=0.71,
                recommendation="RECOMMENDED: Preserves mission continuity while mitigating active GPS fault.",
            )
        elif norm in ("safe_mode", "enter_safe_mode"):
            sim = SimulationResult(
                action_id="safe_mode",
                action_name="Enter Safe Mode",
                predicted_mission_outcome="Controlled hover and stable descent. 100% boundary safety, mission paused.",
                predicted_risk=0.08,
                energy_impact=-0.2,
                residual_uncertainty=0.1,
                expected_recovery_time=4.0,
                mission_continuity=0.00,
                recommendation="FAILSAFE: Zero trajectory hazard; mandatory recovery action if inertial mode fails.",
            )
        else:
            return {
                "success": False,
                "error": f"Unknown action '{action_id}'. Valid options: continue_gps, switch_inertial, safe_mode.",
            }

        return sim.model_dump()


class EvaluatePolicyTool(Tool):
    name = "evaluate_policy"
    description = (
        "Applies deterministic flight governance rules to verify if an action is permitted, "
        "denied, or requires explicit Human-in-the-Loop (HITL) authorization."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action to evaluate: continue_gps, switch_inertial, or safe_mode.",
            },
            "action_id": {
                "type": "string",
                "description": "Alternative key for action identifier.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string"},
            "status": {"type": "string"},
            "allowed": {"type": "boolean"},
            "requires_authorization": {"type": "boolean"},
            "reason": {"type": "string"},
            "risk_tier": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        state = context.simulator.get_state()
        evaluation = context.policy_engine.evaluate_policy(action_id, state)
        return evaluation.model_dump()


class ExecuteActionTool(Tool):
    name = "execute_action"
    description = (
        "Executes an authorized flight response action through the authoritative actuator boundary, "
        "reconfiguring the simulator platform."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action to execute: switch_inertial or safe_mode.",
            },
            "action_id": {
                "type": "string",
                "description": "Alternative key for action identifier.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string"},
            "success": {"type": "boolean"},
            "timestamp": {"type": "number"},
            "previous_mode": {"type": "string"},
            "new_mode": {"type": "string"},
            "details": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        result = context.execution_adapter.execute_action(action_id)
        return result.model_dump()


class VerifyActionTool(Tool):
    name = "verify_action"
    description = (
        "Inspects post-action state invariants and position residuals to verify whether "
        "the executed response successfully restored flight safety."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of executed action being verified.",
            },
            "action_id": {
                "type": "string",
                "description": "Alternative key for action identifier.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "verified": {"type": "boolean"},
            "reason": {"type": "string"},
            "next_action_required": {"type": "boolean"},
            "status": {"type": "string"},
            "position_residual": {"type": "number"},
            "mission_risk": {"type": "number"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        result = context.verification_engine.verify_action(action_id)
        return result.model_dump()


class ReplanTool(Tool):
    name = "replan"
    description = (
        "Initiates dynamic replanning following a verification failure or unpredicted state divergence, "
        "synthesizing updated recovery alternatives."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Reason for replanning trigger (e.g. verification failed).",
            },
            "previous_action": {
                "type": "string",
                "description": "Action that failed verification.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "recommended_action": {"type": "string"},
            "reason": {"type": "string"},
            "action_options": {"type": "array"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        context.simulator.replan_count += 1
        state = context.simulator.get_state()
        reason = arguments.get("reason", "Verification failure in previous response.")
        prev = arguments.get("previous_action", "switch_inertial")

        return {
            "status": "replanned",
            "replan_count": context.simulator.replan_count,
            "recommended_action": "safe_mode",
            "reason": (
                f"Previous action '{prev}' failed verification ({reason}). "
                "Inertial stability cannot guarantee containment. Transitioning to SAFE_MODE (failsafe hover)."
            ),
            "action_options": [
                {
                    "id": "safe_mode",
                    "name": "Enter Safe Mode",
                    "risk": 0.08,
                    "mission_continuity": 0.00,
                    "priority": "HIGH",
                }
            ],
        }
