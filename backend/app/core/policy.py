"""
AEGIS Policy & Governance Gate
Authoritative application rules ensuring safety constraints, human-in-the-loop (HITL)
authorization requirements, and model constraint containment.
"""

from __future__ import annotations
from typing import Dict, Optional, Set
from app.core.models import (
    NavigationMode,
    PolicyEvaluation,
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

    def reset_authorizations(self) -> None:
        self._authorized_actions.clear()

    def authorize_action(self, action_id: str) -> bool:
        normalized = action_id.lower().strip()
        self._authorized_actions.add(normalized)
        return True

    def is_authorized(self, action_id: str) -> bool:
        return action_id.lower().strip() in self._authorized_actions

    def evaluate_policy(self, action_id: str, state: SystemState) -> PolicyEvaluation:
        norm = action_id.lower().strip()

        # Rule 1: Continue GPS
        if norm in ("continue_gps", "continue_gps_assisted"):
            if state.gps_trust < self.GPS_TRUST_HARD_FLOOR or state.residual > self.RESIDUAL_HARD_CEILING:
                return PolicyEvaluation(
                    action_id=action_id,
                    status=PolicyStatus.DENY,
                    allowed=False,
                    requires_authorization=False,
                    reason=(
                        f"POLICY VIOLATION [Rule POL-01]: GPS trust ({state.gps_trust:.2f}) is below minimum "
                        f"safety threshold ({self.GPS_TRUST_HARD_FLOOR}) with critical residual ({state.residual:.1f}m). "
                        "Continuing GPS flight is strictly prohibited."
                    ),
                    risk_tier="EXTREME",
                )
            elif state.gps_trust < 0.70:
                requires_auth = not self.is_authorized(norm)
                return PolicyEvaluation(
                    action_id=action_id,
                    status=PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION if requires_auth else PolicyStatus.ALLOW,
                    allowed=not requires_auth,
                    requires_authorization=requires_auth,
                    reason="GPS degradation detected. Sustained flight requires Operator Authorization.",
                    risk_tier="HIGH",
                )
            return PolicyEvaluation(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                reason="Nominal GPS conditions. Action permitted.",
                risk_tier="LOW",
            )

        # Rule 2: Switch to Inertial Navigation
        elif norm in ("switch_inertial", "switch_to_inertial"):
            # If flight is currently degraded or residual > 2.0m, requires human operator authorization
            if state.residual > 2.0 or state.gps_fault_active:
                if not self.is_authorized(norm):
                    return PolicyEvaluation(
                        action_id=action_id,
                        status=PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION,
                        allowed=False,
                        requires_authorization=True,
                        reason=(
                            "GOVERNANCE GATE [Rule POL-02]: Transitioning navigation filter from GPS to INERTIAL "
                            "in an active degraded scenario alters vehicle control guarantees and requires human authorization."
                        ),
                        risk_tier="MEDIUM",
                    )
                else:
                    return PolicyEvaluation(
                        action_id=action_id,
                        status=PolicyStatus.ALLOW,
                        allowed=True,
                        requires_authorization=False,
                        reason="Human authorization verified for INERTIAL mode switch. Action cleared for execution.",
                        risk_tier="MEDIUM",
                    )
            return PolicyEvaluation(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                reason="Action allowed under standard flight envelope.",
                risk_tier="LOW",
            )

        # Rule 3: Safe Mode / Emergency Failsafe
        elif norm in ("safe_mode", "enter_safe_mode"):
            # Emergency recovery mode is universally pre-authorized when degraded or replanning
            return PolicyEvaluation(
                action_id=action_id,
                status=PolicyStatus.ALLOW,
                allowed=True,
                requires_authorization=False,
                reason=(
                    "EMERGENCY PROTOCOL [Rule POL-03]: Transitioning to SAFE_MODE (hover/controlled hold) "
                    "is authorized as a primary risk mitigation and recovery failsafe."
                ),
                risk_tier="MINIMAL",
            )

        # Default Deny for unknown actions
        return PolicyEvaluation(
            action_id=action_id,
            status=PolicyStatus.DENY,
            allowed=False,
            requires_authorization=False,
            reason=f"Action '{action_id}' is not a recognized or permitted flight operation.",
            risk_tier="HIGH",
        )
