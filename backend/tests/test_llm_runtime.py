"""
Tests for Phase 1B LLM Runtime and Tool Calling Loop
Tests model tool selection, multi-tool turns, malformed argument handling,
unknown tool rejection, budget enforcement, and trace fidelity using FakeLLMProvider.
"""

import json
import pytest
from app.agent.llm_runtime import LLMRuntime
from app.agent.provider import FakeLLMProvider, FallbackDeterministicProvider, ProviderResponse, ToolCallItem
from app.core.execution import ExecutionAdapter
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def runtime_fixture():
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
    fake_provider = FakeLLMProvider()
    runtime = LLMRuntime(
        tool_registry=registry,
        tool_context=context,
        provider=fake_provider,
        max_rounds=8,
        max_tool_calls=10,
    )
    return runtime, fake_provider, sim


def test_model_selects_real_tool_and_result_passed_back(runtime_fixture):
    runtime, fake_provider, sim = runtime_fixture

    # Step 1: Model requests get_system_state
    resp1 = ProviderResponse(
        tool_calls=[
            ToolCallItem(
                id="call_001",
                name="get_system_state",
                arguments={},
            )
        ]
    )
    # Step 2: Model receives result and outputs conclusion
    resp2 = ProviderResponse(
        content="Vehicle is currently in nominal GPS-assisted flight with 100% battery.",
        finish_reason="stop",
    )
    fake_provider.add_response(resp1)
    fake_provider.add_response(resp2)

    result = runtime.run(incident_id="INC-TEST-001", goal="Check system status.")

    assert result.status == "COMPLETED"
    assert result.tool_calls_count == 1
    assert len(result.trace) == 1
    assert result.trace[0]["tool"] == "get_system_state"
    assert result.trace[0]["status"] == "completed"
    assert result.trace[0]["result"]["navigation_mode"] == "GPS_ASSISTED"
    assert result.final_summary == "Vehicle is currently in nominal GPS-assisted flight with 100% battery."

    # Verify conversation history passed back to provider
    last_messages = fake_provider.call_history[-1]
    tool_msg = next((m for m in last_messages if m.get("role") == "tool"), None)
    assert tool_msg is not None
    assert tool_msg["tool_call_id"] == "call_001"
    parsed_content = json.loads(tool_msg["content"])
    assert "navigation_mode" in parsed_content


def test_multiple_tool_calls_in_single_turn(runtime_fixture):
    runtime, fake_provider, sim = runtime_fixture
    sim.inject_gps_fault(initial_bias=6.0)

    # Model requests both get_observations and get_trust in one turn
    resp1 = ProviderResponse(
        tool_calls=[
            ToolCallItem(id="call_obs", name="get_observations", arguments={}),
            ToolCallItem(id="call_trust", name="get_trust", arguments={}),
        ]
    )
    resp2 = ProviderResponse(
        content="Observations confirm divergence; GPS trust is degraded.",
        finish_reason="stop",
    )
    fake_provider.add_response(resp1)
    fake_provider.add_response(resp2)

    result = runtime.run(incident_id="INC-MULTI-001")

    assert result.status == "COMPLETED"
    assert result.tool_calls_count == 2
    assert len(result.trace) == 2
    assert result.trace[0]["tool"] == "get_observations"
    assert result.trace[1]["tool"] == "get_trust"
    assert result.trace[0]["result"]["residual"] > 5.0
    assert result.trace[1]["result"]["gps_trust"] <= 0.98


def test_unknown_or_unauthorized_tool_rejected(runtime_fixture):
    runtime, fake_provider, _ = runtime_fixture

    # Model attempts to call an unauthorized action tool during read-only investigation
    resp1 = ProviderResponse(
        tool_calls=[
            ToolCallItem(id="call_bad", name="execute_action", arguments={"action": "safe_mode"})
        ]
    )
    resp2 = ProviderResponse(
        content="Understood that action execution is unauthorized in read-only phase.",
        finish_reason="stop",
    )
    fake_provider.add_response(resp1)
    fake_provider.add_response(resp2)

    result = runtime.run()

    assert result.status == "COMPLETED"
    assert len(result.trace) == 1
    assert result.trace[0]["status"] == "unauthorized_tool"
    assert "unauthorized" in result.trace[0]["result"]["error"]


def test_malformed_arguments_rejected(runtime_fixture):
    runtime, fake_provider, _ = runtime_fixture

    # Model returns malformed arguments
    resp1 = ProviderResponse(
        tool_calls=[
            ToolCallItem(
                id="call_err",
                name="get_observations",
                arguments={},
                parse_error="Invalid JSON token at position 4",
            )
        ]
    )
    resp2 = ProviderResponse(content="Recovering from parse error.", finish_reason="stop")
    fake_provider.add_response(resp1)
    fake_provider.add_response(resp2)

    result = runtime.run()

    assert len(result.trace) == 1
    assert result.trace[0]["status"] == "malformed_arguments"
    assert "Invalid tool arguments" in result.trace[0]["result"]["error"]


def test_tool_budget_enforced(runtime_fixture):
    runtime, fake_provider, _ = runtime_fixture
    runtime.max_tool_calls = 5

    # Model tries to invoke 4 tools in round 1, and 4 more in round 2
    resp1 = ProviderResponse(
        tool_calls=[
            ToolCallItem(id=f"c_{i}", name="get_observations", arguments={})
            for i in range(4)
        ]
    )
    resp2 = ProviderResponse(
        tool_calls=[
            ToolCallItem(id=f"c_{i+4}", name="get_trust", arguments={})
            for i in range(4)
        ]
    )
    fake_provider.add_response(resp1)
    fake_provider.add_response(resp2)

    result = runtime.run()

    assert result.status == "BUDGET_EXCEEDED"
    # Should have capped invocations without infinite looping
    assert result.tool_calls_count >= 6
    assert any(t["status"] == "budget_exceeded" for t in result.trace)


def test_default_fallback_provider_e2e(runtime_fixture):
    runtime, _, sim = runtime_fixture
    sim.inject_gps_fault(initial_bias=6.5)

    # Use FallbackDeterministicProvider
    fallback = FallbackDeterministicProvider()
    result = runtime.run(
        incident_id="INC-FALLBACK-001",
        goal="Investigate GPS anomaly",
        provider_override=fallback,
    )

    assert result.status == "COMPLETED"
    assert result.tool_calls_count == 5
    tool_sequence = [t["tool"] for t in result.trace]
    assert tool_sequence == [
        "get_system_state",
        "get_observations",
        "get_trust",
        "generate_hypotheses",
        "get_mission_impact",
    ]
    assert "Diagnostic Investigation Complete" in result.final_summary
