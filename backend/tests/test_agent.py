"""
Tests for Phase 1A Deterministic Agent Investigation:
GPS Fault -> Agent Investigation -> 5 Tool Steps -> H1 Selected
"""

import pytest
from app.agent.runtime import AgentRuntime
from app.core.execution import ExecutionAdapter
from app.core.models import MissionStatus
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def runtime():
    sim = DroneSimulator(seed=42)
    policy = PolicyEngine()
    adapter = ExecutionAdapter(sim, policy)
    verifier = VerificationEngine(sim)
    context = ToolContext(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
    )
    registry = create_default_tool_registry()
    return AgentRuntime(registry, context), sim


def test_deterministic_agent_investigation_flow(runtime):
    agent, sim = runtime

    # 1. GPS Fault injected
    sim.inject_gps_fault(initial_bias=6.0)
    assert sim.gps_fault_active is True
    assert sim.mission_status in (MissionStatus.DEGRADED, MissionStatus.CRITICAL)

    # 2. Agent investigation launched
    state = agent.investigate(
        incident_id="INC-PHASE1-001",
        goal="Investigate the navigation integrity incident.",
    )

    # 3. Exactly 5 tool steps executed in canonical order
    assert len(state.events) == 5
    tool_sequence = [event.tool for event in state.events]
    expected_sequence = [
        "get_system_state",
        "get_observations",
        "get_trust",
        "generate_hypotheses",
        "get_mission_impact",
    ]
    assert tool_sequence == expected_sequence

    # 4. Verify each step completed
    for event in state.events:
        assert event.status == "completed"
        assert event.details is not None

    # 5. Verify H1 selected with highest confidence
    hyp_event = state.events[3]
    assert hyp_event.tool == "generate_hypotheses"
    hypotheses = hyp_event.details["hypotheses"]
    assert len(hypotheses) >= 2

    # H1 should be the top hypothesis
    h1 = hypotheses[0]
    assert h1["id"] == "H1"
    assert "GPS Signal Integrity" in h1["title"]
    assert h1["likelihood"] > 0.70

    # Ensure H1 confidence > H2 and H1 confidence > H3
    h2 = next((h for h in hypotheses if h["id"] == "H2"), None)
    h3 = next((h for h in hypotheses if h["id"] == "H3"), None)
    if h2:
        assert h1["likelihood"] > h2["likelihood"]
    if h3:
        assert h1["likelihood"] > h3["likelihood"]

    # 6. Conclusion reached
    assert state.completed is True
    assert state.final_summary is not None
    assert "Investigation Complete" in state.final_summary
