"""
AEGIS Verification Engine
Validates post-action simulator telemetry against safety invariants,
detects execution discrepancies, and triggers deliberate demo recovery failure.
"""

from __future__ import annotations
from app.core.models import NavigationMode, SystemState, VerificationResult
from app.core.risk import RiskEngine
from app.core.simulator import DroneSimulator


class VerificationEngine:
    """
    Evaluates whether an executed action achieved its safety objective.
    Provides deterministic verification failure for recovery demo.
    """

    def __init__(self, simulator: DroneSimulator, deliberate_failure_enabled: bool = True):
        self.simulator = simulator
        self.deliberate_failure_enabled = deliberate_failure_enabled
        self.has_triggered_deliberate_failure = False

    def reset(self) -> None:
        self.has_triggered_deliberate_failure = False

    def verify_action(self, action_id: str) -> VerificationResult:
        state = self.simulator.get_state()
        impact = RiskEngine.evaluate_mission_impact(state)
        norm = action_id.lower().strip()

        # Check deliberate failure demo hook for switch_inertial
        if (
            self.deliberate_failure_enabled
            and norm in ("switch_inertial", "switch_to_inertial")
            and not self.has_triggered_deliberate_failure
        ):
            self.has_triggered_deliberate_failure = True
            return VerificationResult(
                verified=False,
                reason=(
                    "Navigation residual remains above safety threshold (3.6m > 2.0m max allowed) "
                    "due to unmodeled inertial dead-reckoning drift. Navigation stability unverified."
                ),
                next_action_required=True,
                status="failed",
                position_residual=3.6,
                mission_risk=0.48,
            )

        # Verification for SAFE_MODE
        if norm in ("safe_mode", "enter_safe_mode"):
            if state.navigation_mode == NavigationMode.SAFE_MODE:
                return VerificationResult(
                    verified=True,
                    reason="Vehicle successfully stabilized in SAFE_MODE (hover/station keep). Mission risk neutralized.",
                    next_action_required=False,
                    status="safe",
                    position_residual=round(state.residual, 2),
                    mission_risk=impact.operational_risk,
                )
            else:
                return VerificationResult(
                    verified=False,
                    reason=f"Expected SAFE_MODE navigation mode, but vehicle remains in {state.navigation_mode.value}.",
                    next_action_required=True,
                    status="failed",
                    position_residual=round(state.residual, 2),
                    mission_risk=impact.operational_risk,
                )

        # Verification for INERTIAL mode after failure has already occurred
        if norm in ("switch_inertial", "switch_to_inertial"):
            if state.navigation_mode == NavigationMode.INERTIAL and state.residual < 2.0:
                return VerificationResult(
                    verified=True,
                    reason="Inertial navigation active and residual within acceptable bounds.",
                    next_action_required=False,
                    status="safe",
                    position_residual=round(state.residual, 2),
                    mission_risk=impact.operational_risk,
                )
            else:
                return VerificationResult(
                    verified=False,
                    reason=f"Navigation mode {state.navigation_mode.value} residual {state.residual:.1f}m exceeds tolerance.",
                    next_action_required=True,
                    status="failed",
                    position_residual=round(state.residual, 2),
                    mission_risk=impact.operational_risk,
                )

        # General verification check
        if state.residual < 2.0 and impact.operational_risk < 0.20:
            return VerificationResult(
                verified=True,
                reason="System verified within nominal flight boundaries.",
                next_action_required=False,
                status="nominal",
                position_residual=round(state.residual, 2),
                mission_risk=impact.operational_risk,
            )
        else:
            return VerificationResult(
                verified=False,
                reason=f"Operational risk ({impact.operational_risk:.2f}) or residual ({state.residual:.1f}m) exceeds safe limit.",
                next_action_required=True,
                status="failed",
                position_residual=round(state.residual, 2),
                mission_risk=impact.operational_risk,
            )
