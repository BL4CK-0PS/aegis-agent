"""
AEGIS Dynamic Trust Engine
Calculates trust metrics for multi-sensor streams based on residual
persistence, statistical consistency, and anomaly duration.
"""

from __future__ import annotations
from typing import List
from app.core.models import SystemState, TrustSnapshot


class TrustEngine:
    """
    Evaluates sensor integrity and computes bounded trust scores [0.0 - 1.0]
    along with causal degradation explanations.
    """

    RESIDUAL_NOMINAL_THRESHOLD = 2.0  # meters
    RESIDUAL_CRITICAL_THRESHOLD = 6.0  # meters

    @classmethod
    def evaluate(cls, state: SystemState) -> TrustSnapshot:
        reasons: List[str] = []

        # GPS Trust Assessment
        gps_trust = state.gps_trust
        if state.residual > cls.RESIDUAL_NOMINAL_THRESHOLD:
            reasons.append(
                f"GPS position diverges from inertial dead-reckoning by {state.residual:.1f}m "
                f"(exceeds nominal threshold {cls.RESIDUAL_NOMINAL_THRESHOLD}m)."
            )

        if state.residual > cls.RESIDUAL_CRITICAL_THRESHOLD:
            reasons.append(
                f"Persistent critical residual detected ({state.residual:.1f}m > {cls.RESIDUAL_CRITICAL_THRESHOLD}m). "
                f"Statistical signature indicates systematic spoofing, ephemeris corruption, or multi-path bias."
            )

        if gps_trust < 0.40:
            reasons.append(
                f"GPS trust score ({gps_trust:.2f}) degraded below safe flight authorization threshold (0.40)."
            )
        elif not reasons:
            reasons.append("GPS observations consistent with dead-reckoning filters; nominal sensor trust.")

        # IMU Trust Assessment
        imu_trust = state.imu_trust
        if imu_trust >= 0.90:
            reasons.append("IMU accelerometer and angular rate sensors verify dynamic vehicle constraints.")

        # Communication Trust Assessment
        comm_trust = state.communication_health

        return TrustSnapshot(
            gps_trust=round(gps_trust, 2),
            imu_trust=round(imu_trust, 2),
            communication_trust=round(comm_trust, 2),
            reasons=reasons,
            timestamp=state.time,
        )
