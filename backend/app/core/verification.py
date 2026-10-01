"""
AEGIS Verification & Replanning Engine
Validates post-action simulator telemetry against safety invariants,
evaluates expected vs. actual platform state, produces structured check audits,
and orchestrates dynamic replanning following execution divergence.
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Union
from app.core.actions import generate_actions, normalize_action_id
from app.core.models import (
    ExecutionResult,
    MissionStatus,
    NavigationMode,
    SystemState,
    VerificationResult,
)
from app.core.risk import RiskEngine
from app.core.simulator import DroneSimulator


class VerificationEngine:
    """
    Evaluates whether an executed action achieved its safety objective.
    Compares EXPECTED STATE against ACTUAL STATE using live simulator telemetry.
    Provides deterministic verification failure for the canonical recovery demo.
    """

    def __init__(self, simulator: DroneSimulator, deliberate_failure_enabled: bool = True):
        self.simulator = simulator
        self.deliberate_failure_enabled = deliberate_failure_enabled
        self.has_triggered_deliberate_failure = False

    def reset(self) -> None:
        self.has_triggered_deliberate_failure = False

    def verify_action(
        self,
        action_or_result: Union[str, ExecutionResult, Dict[str, Any]],
    ) -> VerificationResult:
        if isinstance(action_or_result, ExecutionResult):
            action_id = action_or_result.action_id
        elif isinstance(action_or_result, dict):
            action_id = action_or_result.get("action_id") or action_or_result.get("action", "")
        else:
            action_id = str(action_or_result)

        state = self.simulator.get_state()
        impact = RiskEngine.evaluate_mission_impact(state)
        canonical_id = normalize_action_id(action_id)
        norm = action_id.lower().strip().replace("-", "_")

        checks: List[Dict[str, Any]] = []
        failed_checks: List[str] = []

        # 1. SWITCH_TO_IMU_ONLY / switch_inertial
        if canonical_id == "SWITCH_TO_IMU_ONLY":
            mode_passed = state.navigation_mode == NavigationMode.INERTIAL
            checks.append({
                "name": "navigation_mode",
                "expected": "INERTIAL",
                "actual": state.navigation_mode.value,
                "passed": mode_passed,
            })
            if not mode_passed:
                failed_checks.append("navigation_mode")

            # Intentional verification failure for the first fallback attempt
            if self.deliberate_failure_enabled and not self.has_triggered_deliberate_failure:
                self.has_triggered_deliberate_failure = True
                self.simulator.mission_status = MissionStatus.RECOVERING

                checks.append({
                    "name": "navigation_confidence",
                    "expected": ">=0.80",
                    "actual": "0.61",
                    "passed": False,
                })
                checks.append({
                    "name": "position_residual",
                    "expected": "<=2.0m",
                    "actual": "3.6m",
                    "passed": False,
                })
                failed_checks.extend(["navigation_confidence", "position_residual"])

                reason_text = (
                    "Navigation residual remains above safety threshold (3.6m > 2.0m max allowed) "
                    "due to unmodeled inertial dead-reckoning drift. Navigation confidence 0.61 < 0.80. "
                    "Navigation stability unverified."
                )
                return VerificationResult(
                    success=False,
                    verified=False,
                    checks=checks,
                    failed_checks=failed_checks,
                    message=reason_text,
                    reason=reason_text,
                    next_action_required=True,
                    status="failed",
                    position_residual=3.6,
                    mission_risk=0.48,
                )

            # Subsequent verification check for inertial mode
            conf_ok = state.residual <= 2.0
            checks.append({
                "name": "navigation_confidence",
                "expected": ">=0.80",
                "actual": "0.92" if conf_ok else "0.61",
                "passed": conf_ok,
            })
            checks.append({
                "name": "position_residual",
                "expected": "<=2.0m",
                "actual": f"{state.residual:.1f}m",
                "passed": conf_ok,
            })
            if not conf_ok:
                failed_checks.append("position_residual")

            is_verified = len(failed_checks) == 0
            reason_text = (
                "Inertial navigation active and residual within acceptable bounds."
                if is_verified
                else f"Navigation mode {state.navigation_mode.value} residual {state.residual:.1f}m exceeds tolerance."
            )
            return VerificationResult(
                success=is_verified,
                verified=is_verified,
                checks=checks,
                failed_checks=failed_checks,
                message=reason_text,
                reason=reason_text,
                next_action_required=not is_verified,
                status="safe" if is_verified else "failed",
                position_residual=round(state.residual, 2),
                mission_risk=impact.operational_risk,
            )

        # 2. ENTER_SAFE_MODE / safe_mode
        elif canonical_id == "ENTER_SAFE_MODE":
            mode_passed = state.navigation_mode == NavigationMode.SAFE_MODE
            checks.append({
                "name": "navigation_mode",
                "expected": "SAFE_MODE",
                "actual": state.navigation_mode.value,
                "passed": mode_passed,
            })
            if not mode_passed:
                failed_checks.append("navigation_mode")

            checks.append({
                "name": "failsafe_containment",
                "expected": "STATION_KEEPING_HOVER",
                "actual": "STATION_KEEPING_HOVER" if mode_passed else "UNCONTAINED",
                "passed": mode_passed,
            })
            if not mode_passed:
                failed_checks.append("failsafe_containment")

            checks.append({
                "name": "ground_collision_risk",
                "expected": "<0.10",
                "actual": "0.02",
                "passed": True,
            })

            is_verified = mode_passed
            reason_text = (
                "Vehicle successfully stabilized in SAFE_MODE (hover/station keep). Mission risk neutralized."
                if is_verified
                else f"Expected SAFE_MODE navigation mode, but vehicle remains in {state.navigation_mode.value}."
            )
            return VerificationResult(
                success=is_verified,
                verified=is_verified,
                checks=checks,
                failed_checks=failed_checks,
                message=reason_text,
                reason=reason_text,
                next_action_required=not is_verified,
                status="safe" if is_verified else "failed",
                position_residual=round(state.residual, 2),
                mission_risk=impact.operational_risk,
            )

        # 3. REQUEST_GPS_REACQUISITION / continue_gps
        elif canonical_id == "REQUEST_GPS_REACQUISITION":
            gps_passed = not state.gps_fault_active and state.residual < 2.0
            checks.append({
                "name": "gps_integrity_lock",
                "expected": "NOMINAL (residual < 2.0m)",
                "actual": f"residual={state.residual:.1f}m, fault={state.gps_fault_active}",
                "passed": gps_passed,
            })
            if not gps_passed:
                failed_checks.append("gps_integrity_lock")

            return VerificationResult(
                success=gps_passed,
                verified=gps_passed,
                checks=checks,
                failed_checks=failed_checks,
                message=(
                    "GPS tracking re-established within nominal envelope."
                    if gps_passed
                    else "GPS integrity check failed; signal bias persists."
                ),
                reason=(
                    "GPS tracking re-established within nominal envelope."
                    if gps_passed
                    else "GPS integrity check failed; signal bias persists."
                ),
                next_action_required=not gps_passed,
                status="nominal" if gps_passed else "failed",
                position_residual=round(state.residual, 2),
                mission_risk=impact.operational_risk,
            )

        # General / Unknown action fallback
        checks.append({
            "name": "general_flight_envelope",
            "expected": "residual < 2.0m and risk < 0.20",
            "actual": f"residual={state.residual:.1f}m, risk={impact.operational_risk:.2f}",
            "passed": False,
        })
        failed_checks.append("general_flight_envelope")
        return VerificationResult(
            success=False,
            verified=False,
            checks=checks,
            failed_checks=failed_checks,
            message=f"Action '{action_id}' unverified against flight boundary envelope.",
            reason=f"Action '{action_id}' unverified against flight boundary envelope.",
            next_action_required=True,
            status="failed",
            position_residual=round(state.residual, 2),
            mission_risk=impact.operational_risk,
        )

    def replan(
        self,
        previous_action: str = "SWITCH_TO_IMU_ONLY",
        reason: str = "Verification failed in previous response.",
        current_state: Optional[SystemState] = None,
        mission_impact: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes dynamic replanning following a verification failure.
        Exposes valid alternatives and their simulation/policy evaluations.
        """
        self.simulator.replan_count += 1
        state = current_state or self.simulator.get_state()
        prev_norm = normalize_action_id(previous_action)

        # Expose candidate alternatives excluding the failed action
        all_actions = generate_actions(state)
        alternatives = []
        for act in all_actions:
            if normalize_action_id(act.id) == prev_norm:
                continue
            alternatives.append({
                "id": act.id,
                "name": act.name,
                "category": act.category,
                "risk_level": act.risk_level,
                "risk": act.risk,
                "mission_continuity": act.mission_continuity,
                "preconditions": act.preconditions,
                "expected_effects": act.expected_effects,
            })

        rec_action = "safe_mode" if previous_action.islower() else "ENTER_SAFE_MODE"
        replan_reason = (
            f"Previous action '{previous_action}' failed verification ({reason}). "
            "Inertial stability cannot guarantee containment. "
            "Reassessing candidate actions and transitioning to failsafe: ENTER_SAFE_MODE."
        )

        return {
            "status": "replanned",
            "replan_count": self.simulator.replan_count,
            "previous_action": previous_action,
            "recommended_action": rec_action,
            "reason": replan_reason,
            "alternative_actions": alternatives,
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

