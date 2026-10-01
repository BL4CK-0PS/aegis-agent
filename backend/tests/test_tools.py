"""
Tests for Tool Registry, Tool Schemas, and Tool Execution
"""

import pytest
from app.core.execution import ExecutionAdapter
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def tool_context():
    sim = DroneSimulator(seed=42, deliberate_failure_enabled=True)
    policy = PolicyEngine()
    adapter = ExecutionAdapter(sim, policy)
    verifier = VerificationEngine(sim, deliberate_failure_enabled=True)
    return ToolContext(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
    )


def test_registry_contains_all_13_tools():
    registry = create_default_tool_registry()
    tools = registry.get_tool_names()

    expected_tools = [
        "get_system_state",
        "get_observations",
        "get_trust",
        "generate_hypotheses",
        "get_mission_impact",
        "get_dependency_graph",
        "generate_actions",
        "simulate_action",
        "evaluate_policy",
        "request_authorization",
        "execute_action",
        "verify_action",
        "replan",
    ]

    for tool in expected_tools:
        assert tool in tools, f"Missing tool in registry: {tool}"
    assert len(tools) == 13


def test_registry_schema_export():
    registry = create_default_tool_registry()
    schemas = registry.get_function_schemas()

    assert len(schemas) == 13
    for s in schemas:
        assert s["type"] == "function"
        assert "name" in s["function"]
        assert "description" in s["function"]
        assert "parameters" in s["function"]


def test_tool_argument_validation(tool_context):
    registry = create_default_tool_registry()

    # Calling an unknown tool returns structured error
    err_res = registry.execute("non_existent_tool", tool_context, {})
    assert err_res["success"] is False
    assert "not found" in err_res["error"]

    # Calling execute_action without action parameter
    res = registry.execute("execute_action", tool_context, {})
    assert res.get("success") is False


def test_simulation_and_counterfactuals(tool_context):
    registry = create_default_tool_registry()
    tool_context.simulator.inject_gps_fault(initial_bias=7.0)

    # Counterfactual 1: continue_gps
    sim_gps = registry.execute("simulate_action", tool_context, {"action": "continue_gps"})
    assert sim_gps["action_id"] == "continue_gps"
    assert sim_gps["predicted_risk"] > 0.80

    # Counterfactual 2: switch_inertial
    sim_inertial = registry.execute("simulate_action", tool_context, {"action": "switch_inertial"})
    assert sim_inertial["action_id"] == "switch_inertial"
    assert sim_inertial["predicted_risk"] < 0.50
    assert sim_inertial["mission_continuity"] > 0.60


def test_deliberate_verification_failure_and_replanning(tool_context):
    registry = create_default_tool_registry()
    tool_context.simulator.inject_gps_fault()

    # Authorize and execute switch_inertial
    tool_context.policy_engine.authorize_action("switch_inertial")
    exec_res = registry.execute("execute_action", tool_context, {"action": "switch_inertial"})
    assert exec_res["success"] is True

    # Verification must deliberately fail for the first inertial switch
    verify_res = registry.execute("verify_action", tool_context, {"action": "switch_inertial"})
    assert verify_res["verified"] is False
    assert verify_res["next_action_required"] is True
    assert "Navigation residual remains above safety threshold" in verify_res["reason"]

    # Agent invokes replan
    replan_res = registry.execute("replan", tool_context, {
        "reason": verify_res["reason"],
        "previous_action": "switch_inertial",
    })
    assert replan_res["status"] == "replanned"
    assert replan_res["recommended_action"] == "safe_mode"

    # Execute safe_mode
    exec_safe = registry.execute("execute_action", tool_context, {"action": "safe_mode"})
    assert exec_safe["success"] is True

    # Verification must succeed for safe_mode
    verify_safe = registry.execute("verify_action", tool_context, {"action": "safe_mode"})
    assert verify_safe["verified"] is True
    assert verify_safe["next_action_required"] is False
