"""
AEGIS Action & Governance Tools
Implements generate_actions, simulate_action, evaluate_policy,
request_authorization, execute_action, verify_action, and replan.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.actions import generate_actions, normalize_action_id
from app.core.models import (
    CandidateAction,
    NavigationMode,
    PolicyEvaluation,
    PolicyResult,
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
        "system state, sensor trust levels, and degradation severity."
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
                        "description": {"type": "string"},
                        "category": {"type": "string"},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}},
                        "risk_level": {"type": "string"},
                        "requires_authorization": {"type": "boolean"},
                        "preconditions": {"type": "array", "items": {"type": "string"}},
                        "expected_effects": {"type": "array", "items": {"type": "string"}},
                        "risk": {"type": "number"},
                        "mission_continuity": {"type": "number"},
                    },
                },
            },
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        state = context.simulator.get_state()
        actions = generate_actions(state)
        return {"actions": [a.model_dump() for a in actions]}


class SimulateActionTool(Tool):
    name = "simulate_action"
    description = (
        "Executes a deterministic counterfactual simulation of a candidate action, "
        "forecasting predicted risk, mission success probability, and capability side effects prior to execution."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action to simulate: SWITCH_TO_IMU_ONLY, REQUEST_GPS_REACQUISITION, or ENTER_SAFE_MODE.",
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
            "predicted_risk": {"type": "number"},
            "mission_success_probability": {"type": "number"},
            "estimated_delay": {"type": "number"},
            "affected_capabilities": {"type": "array", "items": {"type": "string"}},
            "side_effects": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
            "predicted_mission_outcome": {"type": "string"},
            "energy_impact": {"type": "number"},
            "residual_uncertainty": {"type": "number"},
            "expected_recovery_time": {"type": "number"},
            "mission_continuity": {"type": "number"},
            "recommendation": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        sim_engine = context.simulation_engine
        if not sim_engine:
            from app.core.simulation import SimulationEngine
            sim_engine = SimulationEngine(context.simulator)
            context.simulation_engine = sim_engine

        result = sim_engine.simulate(action_id, context.simulator.get_state())
        data = result.model_dump()
        # Preserve caller's input action_id casing/format for backwards compatibility
        data["action_id"] = action_id
        return data


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
                "description": "Identifier of action to evaluate: SWITCH_TO_IMU_ONLY, REQUEST_GPS_REACQUISITION, or ENTER_SAFE_MODE.",
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
            "authorization_status": {"type": "string"},
            "reason": {"type": "string"},
            "risk_tier": {"type": "string"},
            "risk_level": {"type": "string"},
            "violations": {"type": "array", "items": {"type": "string"}},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        state = context.simulator.get_state()
        evaluation = context.policy_engine.evaluate_policy(action_id, state)
        data = evaluation.model_dump()
        data["action_id"] = action_id
        return data


class RequestAuthorizationTool(Tool):
    name = "request_authorization"
    description = (
        "Requests or checks human operator authorization status for high-impact or recovery flight actions."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action requesting authorization.",
            },
            "action_id": {
                "type": "string",
                "description": "Alternative key for action identifier.",
            },
            "justification": {
                "type": "string",
                "description": "Operational justification explaining why authorization is requested.",
            },
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string"},
            "authorized": {"type": "boolean"},
            "authorization_status": {"type": "string"},
            "message": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        is_auth = context.policy_engine.is_authorized(action_id)
        return {
            "action_id": action_id,
            "authorized": is_auth,
            "authorization_status": "APPROVED" if is_auth else "PENDING",
            "message": (
                f"Action '{action_id}' is authorized."
                if is_auth
                else f"Action '{action_id}' is pending operator authorization."
            ),
        }


class ExecuteActionTool(Tool):
    name = "execute_action"
    description = (
        "Executes a validated, authorized flight response action through the authoritative actuator boundary, "
        "enforcing all 6 execution gates."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Identifier of action to execute: SWITCH_TO_IMU_ONLY or ENTER_SAFE_MODE.",
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
            "success": {"type": "boolean"},
            "started_at": {"type": "number"},
            "completed_at": {"type": "number"},
            "previous_mode": {"type": "string"},
            "new_mode": {"type": "string"},
            "state_changes": {"type": "object"},
            "message": {"type": "string"},
            "details": {"type": "string"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action_id = arguments.get("action") or arguments.get("action_id", "")
        if not action_id:
            return {"success": False, "error": "Missing 'action' parameter."}

        result = context.execution_adapter.execute_action(action_id)
        data = result.model_dump()
        data["action_id"] = action_id
        return data


class VerifyActionTool(Tool):
    name = "verify_action"
    description = (
        "Inspects post-action state invariants, position residuals, and navigation confidence against "
        "actual platform telemetry to verify whether the executed response restored flight safety."
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
            "success": {"type": "boolean"},
            "verified": {"type": "boolean"},
            "checks": {"type": "array"},
            "failed_checks": {"type": "array", "items": {"type": "string"}},
            "message": {"type": "string"},
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
        "synthesizing updated recovery alternatives and exposing candidate action options."
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
            "replan_count": {"type": "integer"},
            "recommended_action": {"type": "string"},
            "reason": {"type": "string"},
            "alternative_actions": {"type": "array"},
            "action_options": {"type": "array"},
        },
    }

    def execute(self, context: ToolContext, arguments: Dict[str, Any]) -> Dict[str, Any]:
        reason = arguments.get("reason", "Verification failure in previous response.")
        prev = arguments.get("previous_action", "switch_inertial")
        return context.verification_engine.replan(
            previous_action=prev,
            reason=reason,
            current_state=context.simulator.get_state(),
        )
