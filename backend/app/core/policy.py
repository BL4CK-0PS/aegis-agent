from __future__ import annotations
from typing import Dict, List, Optional, Set
from app.core.actions import normalize_action_id
from app.core.models import (
    AuthorizationStatus,
    NavigationMode,
    PolicyEvaluation,
    PolicyResult,
    PolicyStatus,
    SystemState,
)


class PolicyEngine:
    """
    Deterministic rule engine enforcing flight safety mandates.
    The LLM cannot alter or bypass policy evaluations.
    """

    GPS_TRUST_HARD_FLOOR = 0.40
    RESIDUAL_HARD_CEILING = 4.0

    def __init__(self):
        # Tracks human authorization approvals for specific action IDs
        self._authorized_actions: Set[str] = set()
        self._denied_actions: Set[str] = set()

    def reset_authorizations(self) -> None:
        self._authorized_actions.clear()
        self._denied_actions.clear()

    def authorize_action(self, action_id: str) -> bool:
        normalized = action_id.lower().strip().replace("-", "_")
        canonical = normalize_action_id(action_id)
        self._authorized_actions.add(normalized)
        self._authorized_actions.add(canonical)
        return True

    def deny_action(self, action_id: str) -> bool:
        normalized = action_id.lower().strip().replace("-", "_")
        canonical = normalize_action_id(action_id)
        self._denied_actions.add(normalized)
        self._denied_actions.add(canonical)
        return True

    def is_authorized(self, action_id: str) -> bool:
        normalized = action_id.lower().strip().replace("-", "_")
        canonical = normalize_action_id(action_id)
        return normalized in self._authorized_actions or canonical in self._authorized_actions

    def is_denied(self, action_id: str) -> bool:
        normalized = action_id.lower().strip().replace("-", "_")
        canonical = normalize_action_id(action_id)
        return normalized in self._denied_actions or canonical in self._denied_actions

    def evaluate_policy(
        self,
        action_id: str,
        state: SystemState,
        simulation: Optional[Any] = None,
    ) -> PolicyResult:
        canonical_id = normalize_action_id(action_id)
        norm = action_id.lower().strip().replace("-", "_")

        # Explicit operator denial check
        if self.is_denied(action_id):
            return PolicyResult(
                action_id=action_id,
                status=PolicyStatus.DENY,
                allowed=False,
                requires_authorization=False,
                authorization_status=AuthorizationStatus.DENIED,
                reason=f"Action '{action_id}' was explicitly denied by operator.",
                risk_tier="HIGH",
                risk_level="HIGH",
                violations=["EXPLICIT_OPERATOR_DENIAL"],
            )

        # Rule 1: Continue GPS / GPS Reacquisition
        if canonical_id == "REQUEST_GPS_REACQUISITION":
            if state.gps_trust < self.GPS_TRUST_HARD_FLOOR or state.residual > self.RESIDUAL_HARD_CEILING:
                violations = [
                    f"POL-01: GPS trust ({state.gps_trust:.2f}) is below minimum safety floor ({self.GPS_TRUST_HARD_FLOOR})",
                    f"POL-01: Positional residual ({state.residual:.1f}m) exceeds geofence ceiling ({self.RESIDUAL_HARD_CEILING}m)",
                ]
                return PolicyResult(
                    action_id=action_id,
                    status=PolicyStatus.DENY,
                    allowed=False,
                    requires_authorization=False,
                    authorization_status=AuthorizationStatus.DENIED,
                    reason=(
                        f"POLICY VIOLATION [Rule POL-01]: GPS trust ({state.gps_trust:.2f}) is below minimum "
                        f"safety threshold ({self.GPS_TRUST_HARD_FLOOR}) with critical residual ({state.residual:.1f}m). "
                        "Continuing GPS flight is strictly prohibited."
                    ),
                    risk_tier="EXTREME",
                    risk_level="CRITICAL",
                    violations=violations,
                )
            elif state.gps_trust < 0.70 or state.gps_fault_active:
                requires_auth = not self.is_authorized(action_id)
                auth_status = (
                    AuthorizationStatus.APPROVED if not requires_auth else AuthorizationStatus.PENDING
                )
                return PolicyResult(
                    action_id=action_id,
                    status=PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION if requires_auth else PolicyStatus.ALLOW,
                    allowed=not requires_auth,
                    requires_authorization=requires_auth,
                    authorization_status=auth_status,
                    reason=(
                        "GPS degradation detected. GPS reacquisition requires Operator Authorization."
                        if requires_auth
                        else "Operator authorized GPS reacquisition protocol."
                    ),
                    risk_tier="HIGH",
                    risk_level="HIGH",
                    violations=[],
                )
            return PolicyResult(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                authorization_status=AuthorizationStatus.NOT_REQUIRED,
                reason="Nominal GPS conditions. Action permitted.",
                risk_tier="LOW",
                risk_level="LOW",
                violations=[],
            )

        # Rule 2: Switch to Inertial Navigation
        elif canonical_id == "SWITCH_TO_IMU_ONLY":
            if state.residual > 2.0 or state.gps_fault_active:
                if not self.is_authorized(action_id):
                    return PolicyResult(
                        action_id=action_id,
                        status=PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION,
                        allowed=False,
                        requires_authorization=True,
                        authorization_status=AuthorizationStatus.PENDING,
                        reason=(
                            "GOVERNANCE GATE [Rule POL-02]: Transitioning navigation filter from GPS to INERTIAL "
                            "in an active degraded scenario alters vehicle control guarantees and requires human authorization."
                        ),
                        risk_tier="MEDIUM",
                        risk_level="MEDIUM",
                        violations=[],
                    )
                else:
                    return PolicyResult(
                        action_id=action_id,
                        status=PolicyStatus.ALLOW,
                        allowed=True,
                        requires_authorization=False,
                        authorization_status=AuthorizationStatus.APPROVED,
                        reason="Human authorization verified for INERTIAL mode switch. Action cleared for execution.",
                        risk_tier="MEDIUM",
                        risk_level="LOW",
                        violations=[],
                    )
            return PolicyResult(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                authorization_status=AuthorizationStatus.NOT_REQUIRED,
                reason="Action allowed under standard flight envelope.",
                risk_tier="LOW",
                risk_level="LOW",
                violations=[],
            )

        # Rule 3: Safe Mode / Emergency Failsafe
        elif canonical_id == "ENTER_SAFE_MODE":
            return PolicyResult(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                authorization_status=AuthorizationStatus.NOT_REQUIRED,
                reason=(
                    "EMERGENCY PROTOCOL [Rule POL-03]: Transitioning to SAFE_MODE (hover/controlled hold) "
                    "is authorized as a primary risk mitigation and recovery failsafe."
                ),
                risk_tier="MINIMAL",
                risk_level="MINIMAL",
                violations=[],
            )

        # Default Deny for unknown actions
        return PolicyResult(
            action_id=action_id,
            status=PolicyStatus.DENY,
            allowed=False,
            requires_authorization=False,
            authorization_status=AuthorizationStatus.DENIED,
            reason=f"Action '{action_id}' is not a recognized or permitted flight operation.",
            risk_tier="HIGH",
            risk_level="CRITICAL",
            violations=[f"UNRECOGNIZED_ACTION: '{action_id}'"],
        )
