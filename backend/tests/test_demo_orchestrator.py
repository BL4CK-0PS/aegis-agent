"""
AEGIS Demo Orchestrator Test Suite
Validates the canonical Phase 4 end-to-end orchestration workflow:
1. Demo lifecycle state machine transitions (IDLE -> INCIDENT -> ... -> COMPLETED)
2. Incident injection and diagnostic investigation
3. Evidence, hypotheses, and mission impact generation
4. Candidate action formulation and counterfactual simulations
5. Governance policy gating and authorization
6. Authoritative execution and intentional verification failure
7. Dynamic replanning and recovery failsafe execution
8. Successful verification and platform recovery stabilization
9. Repeatable deterministic execution (multiple runs produce equivalent results)
10. Demo reset functionality (all state cleared)
11. HTTP REST integration tests (POST /api/v1/demo/run, reset, state, trace, events)
12. Security and safety invariants
"""

import pytest
from fastapi.testclient import TestClient

from app.core.execution import ExecutionAdapter
from app.core.models import NavigationMode
from app.core.policy import PolicyEngine
from app.core.simulation import SimulationEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.demo.orchestrator import DemoEvent, DemoOrchestrator, DemoPhase, DemoResult
from app.demo.scenario import CANONICAL_SCENARIO
from app.main import app, demo_orchestrator
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def orchestrator_setup():
    sim = DroneSimulator(seed=42, deliberate_failure_enabled=True)
    policy = PolicyEngine()
    sim_engine = SimulationEngine(sim)
    adapter = ExecutionAdapter(sim, policy, sim_engine)
    verifier = VerificationEngine(sim, deliberate_failure_enabled=True)
    context = ToolContext(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
        simulation_engine=sim_engine,
    )
    registry = create_default_tool_registry()
    orchestrator = DemoOrchestrator(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
        simulation_engine=sim_engine,
        tool_registry=registry,
        tool_context=context,
        scenario=CANONICAL_SCENARIO,
    )
    return orchestrator, sim, policy, verifier


# ==============================================================================
# 1. COMPLETE FLOW UNIT / ORCHESTRATOR TESTS (Items 1-18)
# ==============================================================================

def test_demo_complete_lifecycle(orchestrator_setup):
    orchestrator, sim, policy, verifier = orchestrator_setup

    events_captured = []

    def on_event(ev: DemoEvent):
        events_captured.append(ev)

    # Execute complete decision loop
    result: DemoResult = orchestrator.run(auto_authorize=True, on_event=on_event)

    # 1. Demo completes with valid status
    assert result.status == "COMPLETED"
    assert orchestrator.current_phase == DemoPhase.COMPLETED
    assert result.duration_seconds >= 0.0

    # 2. Incident was injected
    assert result.incident["type"] == "GPS_INTEGRITY_DEGRADATION"
    assert result.incident["bias"] > 5.0

    # 3. Investigation ran
    assert "telemetry" in result.investigation
    assert "observations" in result.investigation
    assert "trust" in result.investigation
    assert result.investigation["observations"]["residual"] > 4.0
    assert result.investigation["trust"]["gps_trust"] < 0.60
    assert result.investigation["trust"]["imu_trust"] >= 0.90

    # 4. Evidence and Hypotheses were generated
    assert len(result.hypotheses) >= 2
    assert "GPS" in result.hypotheses[0]["title"]

    # 5. Mission impact calculated
    assert result.mission_impact["operational_risk"] > 0.70
    assert result.mission_impact["recommendation_urgency"] in ("HIGH", "IMMEDIATE")

    # 6. Actions generated (3 canonical alternatives)
    assert len(result.actions) == 3
    action_ids = [a["id"] for a in result.actions]
    assert "SWITCH_TO_IMU_ONLY" in action_ids
    assert "REQUEST_GPS_REACQUISITION" in action_ids
    assert "ENTER_SAFE_MODE" in action_ids

    # 7. Actions simulated
    assert "primary" in result.simulation
    assert "comparisons" in result.simulation
    assert len(result.simulation["comparisons"]) == 3
    assert result.simulation["primary"]["action_id"] == "SWITCH_TO_IMU_ONLY"

    # 8. Policy evaluated
    assert "primary" in result.policy
    assert result.policy["primary"]["status"] in ("REQUIRES_HUMAN_AUTHORIZATION", "ALLOW")

    # 9. Execution 1 ran
    assert result.execution["attempt_1"]["success"] is True
    assert result.execution["attempt_1"]["new_mode"] == "INERTIAL"

    # 10. Verification 1 deliberately failed
    assert result.verification["attempt_1_failure"]["verified"] is False
    assert result.verification["attempt_1_failure"]["status"] == "failed"
    assert "navigation_confidence" in result.verification["attempt_1_failure"]["failed_checks"]

    # 11. Replanning occurred
    assert result.replanning["status"] == "replanned"
    assert result.replanning["replan_count"] >= 1
    assert result.replanning["recommended_action"] in ("ENTER_SAFE_MODE", "safe_mode")

    # 12. Execution 2 (replacement failsafe) ran
    assert result.execution["attempt_2"]["success"] is True
    assert result.execution["attempt_2"]["new_mode"] == "SAFE_MODE"

    # 13. Verification 2 succeeded
    assert result.verification["attempt_2_success"]["verified"] is True
    assert result.verification["attempt_2_success"]["status"] == "safe"

    # 14. Recovery state
    assert result.recovery["status"] == "RECOVERED"
    assert result.final_state["navigation_mode"] == NavigationMode.SAFE_MODE

    # 15. Complete trace audit
    tools_in_trace = [t["tool"] for t in result.trace]
    assert "inject_gps_fault" in tools_in_trace
    assert "get_system_state" in tools_in_trace
    assert "get_observations" in tools_in_trace
    assert "get_trust" in tools_in_trace
    assert "generate_hypotheses" in tools_in_trace
    assert "get_mission_impact" in tools_in_trace
    assert "generate_actions" in tools_in_trace
    assert "simulate_action" in tools_in_trace
    assert "evaluate_policy" in tools_in_trace
    assert "execute_action" in tools_in_trace
    assert "verify_action" in tools_in_trace
    assert "replan" in tools_in_trace

    # 16. Events captured
    event_names = [e.event for e in events_captured]
    assert "demo_started" in event_names
    assert "incident_injected" in event_names
    assert "actions_generated" in event_names
    assert "verification_failed" in event_names
    assert "replan_started" in event_names
    assert "verification_succeeded" in event_names
    assert "demo_completed" in event_names


def test_demo_reset_functionality(orchestrator_setup):
    orchestrator, sim, policy, verifier = orchestrator_setup

    # Run once
    orchestrator.run(auto_authorize=True)
    assert orchestrator.current_phase == DemoPhase.COMPLETED
    assert len(orchestrator.trace) > 10

    # Reset
    reset_res = orchestrator.reset()
    assert reset_res["status"] == "reset_success"
    assert orchestrator.current_phase == DemoPhase.IDLE
    assert len(orchestrator.trace) == 0
    assert len(orchestrator.events) == 0

    # Simulator returned to nominal baseline
    nominal_state = sim.get_state()
    assert nominal_state.navigation_mode == NavigationMode.GPS_ASSISTED
    assert nominal_state.gps_fault_active is False
    assert nominal_state.residual < 0.5
    assert nominal_state.gps_trust >= 0.95


def test_demo_repeatability(orchestrator_setup):
    """Verifies that running the demo twice produces identical deterministic results."""
    orchestrator, sim, policy, verifier = orchestrator_setup

    res1 = orchestrator.run(auto_authorize=True)
    res2 = orchestrator.run(auto_authorize=True)

    assert res1.status == res2.status == "COMPLETED"
    assert res1.selected_action == res2.selected_action == "ENTER_SAFE_MODE"
    assert res1.verification["attempt_1_failure"]["verified"] == res2.verification["attempt_1_failure"]["verified"] is False
    assert res1.verification["attempt_2_success"]["verified"] == res2.verification["attempt_2_success"]["verified"] is True
    assert len(res1.trace) == len(res2.trace)


# ==============================================================================
# 2. REST API INTEGRATION TESTS (Item 15)
# ==============================================================================

def test_api_demo_run_endpoint():
    client = TestClient(app)

    # 1. Reset first
    res_reset = client.post("/api/v1/demo/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "reset_success"

    # 2. POST /api/v1/demo/run
    res_run = client.post("/api/v1/demo/run", params={"auto_authorize": True})
    assert res_run.status_code == 200

    data = res_run.json()
    assert data["status"] == "COMPLETED"
    assert data["demo_id"].startswith("DEMO-")

    # Verify trace structure
    trace = data["trace"]
    tools_called = [step["tool"] for step in trace]

    # Verify trace contains investigation
    assert "get_system_state" in tools_called
    assert "get_observations" in tools_called
    assert "get_trust" in tools_called

    # Verify trace contains simulation
    assert "simulate_action" in tools_called

    # Verify trace contains policy
    assert "evaluate_policy" in tools_called

    # Verify trace contains execution
    assert "execute_action" in tools_called

    # Verify trace contains verification failure
    verify_steps = [s for s in trace if s["tool"] == "verify_action"]
    assert len(verify_steps) >= 2
    assert any(s["status"] == "FAILED" for s in verify_steps)

    # Verify trace contains replanning
    assert "replan" in tools_called

    # Verify trace contains final successful verification
    assert any(s["status"] == "COMPLETED" for s in verify_steps)


def test_api_demo_state_and_trace_endpoints():
    client = TestClient(app)

    client.post("/api/v1/demo/run")

    # GET /api/v1/demo/state
    res_state = client.get("/api/v1/demo/state")
    assert res_state.status_code == 200
    state_data = res_state.json()
    assert state_data["phase"] == "COMPLETED"
    assert state_data["completed"] is True
    assert state_data["total_steps"] > 10

    # GET /api/v1/demo/trace
    res_trace = client.get("/api/v1/demo/trace")
    assert res_trace.status_code == 200
    trace_data = res_trace.json()
    assert isinstance(trace_data, list)
    assert len(trace_data) > 10

    # GET /api/v1/demo/events
    res_events = client.get("/api/v1/demo/events")
    assert res_events.status_code == 200
    events_data = res_events.json()
    assert isinstance(events_data, list)
    assert len(events_data) > 10


# ==============================================================================
# 3. SAFETY AND GOVERNANCE INVARIANTS (Item 16)
# ==============================================================================

def test_safety_invariants_during_demo(orchestrator_setup):
    orchestrator, sim, policy, verifier = orchestrator_setup

    # Reset
    orchestrator.reset()
    initial_mode = sim.navigation_mode

    # Invariant: Simulation does not alter real state
    orchestrator.simulation_engine.simulate("SWITCH_TO_IMU_ONLY")
    assert sim.navigation_mode == initial_mode

    # Invariant: Execution requires valid policy & authorization
    sim.inject_gps_fault()
    unauth_res = orchestrator.execution_adapter.execute_action("SWITCH_TO_IMU_ONLY")
    assert unauth_res.success is False
    assert sim.navigation_mode == initial_mode

    # Invariant: Unknown action cannot execute
    fake_res = orchestrator.execution_adapter.execute_action("INVALID_ACTION_XYZ")
    assert fake_res.success is False
    assert sim.navigation_mode == initial_mode
