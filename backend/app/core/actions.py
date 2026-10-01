"""
AEGIS Action Engine
Defines candidate operational response models, canonical action definitions,
dynamic action generation based on live telemetry, and strict precondition validation.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.models import (
    ActionCategory,
    CandidateAction,
    NavigationMode,
    PreconditionCheck,
    PreconditionResult,
    RiskLevel,
    SystemState,
)

CANONICAL_ACTION_MAP: Dict[str, str] = {
    "SWITCH_TO_IMU_ONLY": "SWITCH_TO_IMU_ONLY",
    "SWITCH_INERTIAL": "SWITCH_TO_IMU_ONLY",
    "SWITCH_TO_INERTIAL": "SWITCH_TO_IMU_ONLY",
    "IMU_ONLY": "SWITCH_TO_IMU_ONLY",
    "REQUEST_GPS_REACQUISITION": "REQUEST_GPS_REACQUISITION",
    "CONTINUE_GPS": "REQUEST_GPS_REACQUISITION",
    "CONTINUE_GPS_ASSISTED": "REQUEST_GPS_REACQUISITION",
    "GPS_REACQUISITION": "REQUEST_GPS_REACQUISITION",
    "ENTER_SAFE_MODE": "ENTER_SAFE_MODE",
    "SAFE_MODE": "ENTER_SAFE_MODE",
}

CANONICAL_ACTION_IDS = ["SWITCH_TO_IMU_ONLY", "REQUEST_GPS_REACQUISITION", "ENTER_SAFE_MODE"]


def normalize_action_id(action_id: str) -> str:
    """Normalizes action identifier to canonical uppercase token."""
    cleaned = action_id.upper().strip().replace("-", "_")
    return CANONICAL_ACTION_MAP.get(cleaned, cleaned)


def is_valid_action(action_id: str) -> bool:
    """Checks whether an action exists in the system registry."""
    return normalize_action_id(action_id) in CANONICAL_ACTION_IDS


def generate_actions(
    state: SystemState,
    observations: Optional[Any] = None,
    trust: Optional[Any] = None,
    hypotheses: Optional[Any] = None,
    mission_impact: Optional[Any] = None,
) -> List[CandidateAction]:
    """
    Deterministically generates the candidate recovery actions from actual system state.
    Generates 3 canonical alternatives:
      1. SWITCH_TO_IMU_ONLY
      2. REQUEST_GPS_REACQUISITION
      3. ENTER_SAFE_MODE
    """
    gps_degraded = state.gps_fault_active or state.gps_trust < 0.60 or state.residual > 2.0
    imu_healthy = state.imu_trust >= 0.70

    actions: List[CandidateAction] = []

    # 1. SWITCH_TO_IMU_ONLY
    actions.append(
        CandidateAction(
            id="SWITCH_TO_IMU_ONLY",
            name="SWITCH_TO_IMU_ONLY",
            description="Isolate corrupted GPS signal and engage IMU dead-reckoning filter.",
            category=ActionCategory.NAVIGATION_RECONFIGURATION.value,
            required_capabilities=[
                "IMU_SENSING",
                "ATTITUDE_ESTIMATION",
                "INERTIAL_DEAD_RECKONING",
            ],
            risk_level=RiskLevel.LOW.value if imu_healthy else RiskLevel.HIGH.value,
            requires_authorization=False,
            preconditions=[
                "imu_trust >= 0.70",
                "navigation_mode != INERTIAL",
                "propulsion_available == True",
            ],
            expected_effects=[
                "GPS dependency eliminated",
                "Navigation continues via inertial propagation",
                "Trajectory drift accumulation over time",
                "Small mission delay (+18 sec)",
            ],
            risk=0.25 if imu_healthy else 0.85,
            mission_continuity=0.71,
            target_mode=NavigationMode.INERTIAL,
        )
    )

    # 2. REQUEST_GPS_REACQUISITION
    actions.append(
        CandidateAction(
            id="REQUEST_GPS_REACQUISITION",
            name="REQUEST_GPS_REACQUISITION",
            description="Attempt GPS signal reacquisition and filter recalibration while holding course.",
            category=ActionCategory.SENSOR_MANAGEMENT.value,
            required_capabilities=[
                "GPS_SIGNAL_ACQUISITION",
                "EPHEMERIS_VALIDATION",
            ],
            risk_level=RiskLevel.MEDIUM.value if gps_degraded else RiskLevel.LOW.value,
            requires_authorization=True,
            preconditions=[
                "communication_health >= 0.50",
                "navigation_mode != SAFE_MODE",
                "propulsion_available == True",
            ],
            expected_effects=[
                "Potential GPS signal recovery",
                "Continued trajectory divergence if spoofing persists",
                "Moderate mission delay (+2.4 min)",
            ],
            risk=0.65 if gps_degraded else 0.05,
            mission_continuity=0.35 if gps_degraded else 0.95,
            target_mode=NavigationMode.GPS_ASSISTED,
        )
    )

    # 3. ENTER_SAFE_MODE
    actions.append(
        CandidateAction(
            id="ENTER_SAFE_MODE",
            name="ENTER_SAFE_MODE",
            description="Arrest forward velocity into stationary hover / controlled emergency descent.",
            category=ActionCategory.FAILSAFE.value,
            required_capabilities=[
                "FLIGHT_CONTROL",
                "HOVER_STABILIZATION",
                "PROPULSION",
            ],
            risk_level=RiskLevel.LOW.value,
            requires_authorization=False,
            preconditions=[
                "propulsion_available == True",
                "altitude >= 1.0",
            ],
            expected_effects=[
                "Vehicle transitions to stationary hover",
                "Zero trajectory geofence departure risk",
                "Mission progress halted",
                "Extended mission delay (+4.8 min)",
            ],
            risk=0.05,
            mission_continuity=0.00,
            target_mode=NavigationMode.SAFE_MODE,
        )
    )

    return actions


def validate_preconditions(action_id: str, state: SystemState) -> PreconditionResult:
    """
    Validates preconditions for an action against current platform state:
    - Required sensor availability
    - Current navigation mode compatibility
    - Mission state and constraints
    - Platform safety constraints
    """
    canonical_id = normalize_action_id(action_id)

    if canonical_id not in CANONICAL_ACTION_IDS:
        return PreconditionResult(
            valid=False,
            reason=f"Unknown action '{action_id}'. Action does not exist in registry.",
            checks=[
                PreconditionCheck(
                    name="action_existence",
                    required="known_action",
                    actual=action_id,
                    passed=False,
                    description="Action identifier must be registered in the system.",
                )
            ],
        )

    checks: List[PreconditionCheck] = []

    if canonical_id == "SWITCH_TO_IMU_ONLY":
        # 1. IMU Availability & Trust
        imu_ok = state.imu_trust >= 0.70
        checks.append(
            PreconditionCheck(
                name="sensor_imu_availability",
                required="imu_trust >= 0.70",
                actual=f"{state.imu_trust:.2f}",
                passed=imu_ok,
                description="IMU sensor must be operational with trust above minimum safety floor.",
            )
        )

        # 2. Mode compatibility
        mode_ok = state.navigation_mode != NavigationMode.SAFE_MODE
        checks.append(
            PreconditionCheck(
                name="navigation_mode_compatibility",
                required="mode != SAFE_MODE",
                actual=state.navigation_mode.value,
                passed=mode_ok,
                description="Cannot transition to inertial flight while locked in SAFE_MODE.",
            )
        )

        # 3. Energy constraint
        energy_ok = state.energy > 5.0
        checks.append(
            PreconditionCheck(
                name="battery_energy_sufficiency",
                required="energy > 5.0%",
                actual=f"{state.energy:.1f}%",
                passed=energy_ok,
                description="Battery energy must be sufficient to sustain forward flight.",
            )
        )

        failed = [c for c in checks if not c.passed]
        if failed:
            return PreconditionResult(
                valid=False,
                reason=f"Preconditions failed for {canonical_id}: {failed[0].name} ({failed[0].description})",
                checks=checks,
            )
        return PreconditionResult(
            valid=True,
            reason=f"All preconditions satisfied for {canonical_id}.",
            checks=checks,
        )

    elif canonical_id == "REQUEST_GPS_REACQUISITION":
        # 1. Hardware & Comm Health
        comm_ok = state.communication_health >= 0.30
        checks.append(
            PreconditionCheck(
                name="communication_channel_health",
                required="comm_health >= 0.30",
                actual=f"{state.communication_health:.2f}",
                passed=comm_ok,
                description="Telemetry uplink/downlink must be functional for ephemeris re-sync.",
            )
        )

        # 2. Mode compatibility
        mode_ok = state.navigation_mode != NavigationMode.SAFE_MODE
        checks.append(
            PreconditionCheck(
                name="navigation_mode_compatibility",
                required="mode != SAFE_MODE",
                actual=state.navigation_mode.value,
                passed=mode_ok,
                description="Cannot request GPS tracking during station-keeping SAFE_MODE.",
            )
        )

        failed = [c for c in checks if not c.passed]
        if failed:
            return PreconditionResult(
                valid=False,
                reason=f"Preconditions failed for {canonical_id}: {failed[0].name} ({failed[0].description})",
                checks=checks,
            )
        return PreconditionResult(
            valid=True,
            reason=f"All preconditions satisfied for {canonical_id}.",
            checks=checks,
        )

    elif canonical_id == "ENTER_SAFE_MODE":
        # 1. Propulsion / Altitude
        alt_ok = state.altitude >= 0.5
        checks.append(
            PreconditionCheck(
                name="platform_airborne",
                required="altitude >= 0.5m",
                actual=f"{state.altitude:.1f}m",
                passed=alt_ok,
                description="Vehicle must be airborne to enter station-keeping hover.",
            )
        )

        failed = [c for c in checks if not c.passed]
        if failed:
            return PreconditionResult(
                valid=False,
                reason=f"Preconditions failed for {canonical_id}: {failed[0].name} ({failed[0].description})",
                checks=checks,
            )
        return PreconditionResult(
            valid=True,
            reason=f"All preconditions satisfied for {canonical_id}.",
            checks=checks,
        )

    return PreconditionResult(valid=False, reason="Unhandled action evaluation.", checks=checks)
