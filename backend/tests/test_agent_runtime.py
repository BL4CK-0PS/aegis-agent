"""
Tests for AgentRuntime: Tool Calling, Governance Pausing, Deliberate Failure, and Recovery Replan
"""

import pytest
from app.agent.runtime import AgentRuntime
from app.core.execution import ExecutionAdapter
from app.core.models import NavigationMode
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def runtime_setup():
    sim = DroneSimulator(seed=42, deliberate_failure_enabled=True)
    policy = PolicyEngine()
    adapter = ExecutionAdapter(sim, policy)
    verifier = VerificationEngine(sim, deliberate_failure_enabled=True)
    context = ToolContext(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
    )
    registry = create_default_tool_registry()
    runtime = AgentRuntime(registry, context)
    return runtime, sim, policy


def test_agent_investigation_pauses_for_human_authorization(runtime_setup):
    runtime, sim, policy = runtime_setup
    sim.inject_gps_fault(initial_bias=7.0)

    # Run without auto-authorization
    state = runtime.run(incident_id="INC-TEST-001", auto_authorize=False)

    # Agent should have gathered evidence, simulated counterfactuals, evaluated policy,
    # and paused when switch_inertial required Human-in-the-Loop authorization!
    assert state.waiting_for_authorization is True
    assert state.pending_action in ("switch_inertial", "switch_to_inertial")
    assert state.tool_calls_count >= 8

    # Ensure tool calls were logged as events
    tool_names = [e.tool for e in state.events]
    assert "get_system_state" in tool_names
    assert "get_observations" in tool_names
    assert "get_trust" in tool_names
    assert "generate_hypotheses" in tool_names
    assert "get_mission_impact" in tool_names
    assert "get_dependency_graph" in tool_names
    assert "simulate_action" in tool_names
    assert "evaluate_policy" in tool_names


def test_agent_full_recovery_loop_with_authorization(runtime_setup):
    runtime, sim, policy = runtime_setup
    sim.inject_gps_fault(initial_bias=7.0)

    # Step 1: Run to authorization gate
    state = runtime.run(incident_id="INC-TEST-001", auto_authorize=False)
    assert state.waiting_for_authorization is True

    # Step 2: Human operator authorizes the action via operator interface
    resumed_state = runtime.authorize(action_id="switch_inertial", auto_resume=True)

    # Loop should have completed the entire flow:
    # 1. Execute switch_inertial
    # 2. Verify -> FAIL (deliberate verification failure)
    # 3. Replan
    # 4. Evaluate safe_mode
    # 5. Execute safe_mode
    # 6. Verify -> SUCCESS
    # 7. Final incident summary
    assert resumed_state.completed is True
    assert resumed_state.waiting_for_authorization is False
    assert resumed_state.replan_count >= 1
    assert resumed_state.current_step <= runtime.MAX_STEPS

    # Verify final vehicle mode is SAFE_MODE
    assert sim.navigation_mode == NavigationMode.SAFE_MODE

    # Check last verification result is safe/verified
    assert resumed_state.last_verification_result is not None
    assert resumed_state.last_verification_result.get("verified") is True

    # Check final summary text
    assert resumed_state.final_summary is not None
    assert "RECOVERED" in resumed_state.final_summary
    assert "SAFE_MODE" in resumed_state.final_summary


def test_agent_auto_authorized_run(runtime_setup):
    runtime, sim, policy = runtime_setup
    sim.inject_gps_fault(initial_bias=6.0)

    state = runtime.run(incident_id="INC-AUTO-001", auto_authorize=True)
    assert state.completed is True
    assert state.replan_count >= 1
    assert sim.navigation_mode == NavigationMode.SAFE_MODE
