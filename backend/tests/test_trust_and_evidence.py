"""
Tests for TrustEngine, EvidenceEngine, and Hypothesis Formulation
"""

import pytest
from app.core.evidence import EvidenceEngine
from app.core.simulator import DroneSimulator
from app.core.trust import TrustEngine


def test_trust_engine_under_fault():
    sim = DroneSimulator(seed=42)
    nominal_state = sim.get_state()
    nominal_trust = TrustEngine.evaluate(nominal_state)

    assert nominal_trust.gps_trust >= 0.95
    assert nominal_trust.imu_trust >= 0.90
    assert any("nominal" in r.lower() for r in nominal_trust.reasons)

    # Inject fault and advance
    sim.inject_gps_fault(initial_bias=7.0)
    for _ in range(3):
        sim.tick()

    fault_state = sim.get_state()
    degraded_trust = TrustEngine.evaluate(fault_state)

    assert degraded_trust.gps_trust < 0.45
    assert degraded_trust.imu_trust >= 0.90
    assert any("diverges" in r.lower() or "critical" in r.lower() for r in degraded_trust.reasons)


def test_evidence_extraction():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault(initial_bias=6.5)
    state = sim.get_state()

    evidence = EvidenceEngine.extract_evidence(state)
    assert len(evidence) == 4

    evidence_ids = {e.id for e in evidence}
    assert {"E01", "E02", "E03", "E04"} == evidence_ids

    # E01 residual should reflect critical severity
    e01 = next(e for e in evidence if e.id == "E01")
    assert e01.severity in ("HIGH", "CRITICAL")
    assert "divergence" in e01.interpretation.lower()


def test_competing_hypotheses_ranking():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault(initial_bias=8.0)
    state = sim.get_state()

    hypotheses = EvidenceEngine.generate_hypotheses(state)
    assert len(hypotheses) == 3

    # Primary hypothesis should be GPS integrity / spoofing with highest likelihood
    top_hyp = hypotheses[0]
    assert top_hyp.id == "H1"
    assert "GPS Signal Integrity" in top_hyp.title
    assert top_hyp.likelihood >= 0.70
    assert "E01" in top_hyp.supporting_evidence
