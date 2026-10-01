"""
AEGIS Evidence Fusion & Competing Hypotheses Engine
Extracts verified evidence items and synthesizes competing incident hypotheses
with probabilistic likelihood scoring.
"""

from __future__ import annotations
from typing import List, Tuple
from app.core.models import EvidenceItem, Hypothesis, SystemState


class EvidenceEngine:
    """
    Extracts deterministic evidence items from telemetry and formulates
    competing causal hypotheses.
    """

    @classmethod
    def extract_evidence(cls, state: SystemState) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        # Residual Evidence
        residual_severity = "LOW"
        if state.residual > 6.0:
            residual_severity = "CRITICAL"
        elif state.residual > 2.0:
            residual_severity = "HIGH"

        items.append(
            EvidenceItem(
                id="E01",
                source="GPS / IMU Comparative Filter",
                metric="Position Residual",
                value=f"{state.residual:.2f} m",
                interpretation=(
                    "Euclidean divergence between GPS receiver solution and inertial dead-reckoning trajectory."
                ),
                severity=residual_severity,
                confidence=0.94 if state.residual > 2.0 else 0.98,
                relationship="Supports H1 (GPS integrity degradation)" if state.residual > 2.0 else "Supports H0 (Nominal)",
            )
        )

        # GPS Trust Evidence
        trust_severity = "NOMINAL"
        if state.gps_trust < 0.40:
            trust_severity = "CRITICAL"
        elif state.gps_trust < 0.70:
            trust_severity = "HIGH"

        items.append(
            EvidenceItem(
                id="E02",
                source="Dynamic Trust Engine",
                metric="GPS Trust Index",
                value=f"{state.gps_trust:.2f}",
                interpretation="Statistical integrity confidence score for Global Positioning System data.",
                severity=trust_severity,
                confidence=0.92,
                relationship="Supports H1 (GPS integrity degradation)" if state.gps_trust < 0.7 else "Supports H0 (Nominal)",
            )
        )

        # Anomaly Detector Evidence
        items.append(
            EvidenceItem(
                id="E03",
                source="Telemetry Anomaly Detector",
                metric="Anomaly Score",
                value=f"{state.anomaly_score:.3f}",
                interpretation="Normalized anomaly intensity combining residual amplitude and persistence.",
                severity="HIGH" if state.anomaly_score > 0.6 else "NOMINAL",
                confidence=0.89,
                relationship="Supports H1 (GPS integrity degradation)" if state.anomaly_score > 0.4 else "Supports H0 (Nominal)",
            )
        )

        # IMU Kinematic Health
        items.append(
            EvidenceItem(
                id="E04",
                source="Inertial Measurement Unit (IMU)",
                metric="Kinematic Consistency",
                value=f"{state.imu_trust:.2f}",
                interpretation="High internal consistency across triple-axis accelerometers and gyroscopes.",
                severity="NOMINAL" if state.imu_trust > 0.85 else "HIGH",
                confidence=0.96,
                relationship="Contradicts H3 (Inertial drift)" if state.imu_trust > 0.85 else "Supports H3 (Inertial drift)",
            )
        )

        return items

    @classmethod
    def generate_hypotheses(cls, state: SystemState) -> List[Hypothesis]:
        """
        Formulates competing hypotheses with likelihoods normalized to 1.0.
        """
        if state.residual > 2.0:
            # Significant anomaly detected
            # Likelihood shifts heavily to GPS integrity failure as residual rises
            if state.residual > 5.0:
                h1_prob = 0.91
                h2_prob = 0.06
                h3_prob = 0.03
            else:
                h1_prob = 0.75
                h2_prob = 0.18
                h3_prob = 0.07

            return [
                Hypothesis(
                    id="H1",
                    title="GPS Signal Integrity Degradation / Spoofing / Multipath",
                    likelihood=h1_prob,
                    explanation=(
                        f"Significant divergence ({state.residual:.1f}m) while IMU retains high confidence "
                        f"({state.imu_trust:.2f}) indicates external GPS signal corruption, ephemeris bias, or spoofing."
                    ),
                    supporting_evidence=["E01", "E02", "E03"],
                ),
                Hypothesis(
                    id="H2",
                    title="Transient Environmental Observation Noise",
                    likelihood=h2_prob,
                    explanation=(
                        "Temporary atmospheric interference or signal attenuation causing short-duration variance."
                    ),
                    supporting_evidence=["E01"],
                ),
                Hypothesis(
                    id="H3",
                    title="Inertial Dead-Reckoning Integration Drift",
                    likelihood=h3_prob,
                    explanation=(
                        "Internal gyro bias accumulation or accelerometer scale-factor drift causing divergence."
                    ),
                    supporting_evidence=["E04"],
                ),
            ]
        else:
            # Nominal operating conditions
            return [
                Hypothesis(
                    id="H0",
                    title="Nominal Navigation Performance",
                    likelihood=0.96,
                    explanation="All sensors operating within standard deviation tolerances with consistent fusion.",
                    supporting_evidence=["E01", "E02", "E04"],
                ),
                Hypothesis(
                    id="H2",
                    title="Minor Sensor Noise",
                    likelihood=0.04,
                    explanation="Standard Gaussian sensor variance observed.",
                    supporting_evidence=["E01"],
                ),
            ]
