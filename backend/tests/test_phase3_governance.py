"""
AEGIS Phase 3 Deterministic Test Suite
Validates the complete Action, Simulation & Governance Engine:
1. Action generation & canonical models
2. Precondition validation & rejection
3. Simulation isolation (no mutation on real simulator)
4. Policy evaluation & risk tiers
5. Authorization enforcement (PENDING vs APPROVED vs DENIED)
6. Execution gates (6-gate actuator containment)
7. Verification checks (expected vs actual state)
8. Intentional verification failure (controlled demo step)
9. Dynamic replanning & candidate alternative exposure
10. Critical safety invariants (DENIED / PENDING cannot execute)
11. Complete GPS incident end-to-end lifecycle
"""

import pytest
from app.core.actions import (
    CANONICAL_ACTION_IDS,
    generate_actions,
    is_valid_action,
    normalize_action_id,
    validate_preconditions,
)
from app.core.execution import ExecutionAdapter
from app.core.models import (
    ActionCategory,
    AuthorizationStatus,
    NavigationMode,
    PolicyStatus,
    RiskLevel,
    SystemState,
)
from app.core.policy import PolicyEngine
from app.core.risk import RiskEngine
from app.core.simulation import SimulationEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


@pytest.fixture
def system_setup():
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
    return sim, policy, sim_engine, adapter, verifier, context, registry


# ==============================================================================
# 1. ACTION MODEL & GENERATION
# ==============================================================================

def test_action_generation(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=7.0)
    state = sim.get_state()

    actions = generate_actions(state)
    assert len(actions) == 3

    action_ids = [a.id for a in actions]
    assert "SWITCH_TO_IMU_ONLY" in action_ids
    assert "REQUEST_GPS_REACQUISITION" in action_ids
    assert "ENTER_SAFE_MODE" in action_ids

    # Verify structured fields
    for a in actions:
        assert a.id in CANONICAL_ACTION_IDS
        assert len(a.name) > 0
        assert len(a.description) > 0
        assert a.category in [c.value for c in ActionCategory]
        assert a.risk_level in [r.value for r in RiskLevel]
        assert isinstance(a.requires_authorization, bool)
        assert len(a.preconditions) > 0
        assert len(a.expected_effects) > 0
        assert 0.0 <= a.risk <= 1.0
        assert 0.0 <= a.mission_continuity <= 1.0


# ==============================================================================
# 2. PRECONDITION VALIDATION
# ==============================================================================

def test_invalid_preconditions_rejection(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    state = sim.get_state()

    # 1. Unknown action fails preconditions
    res_unknown = validate_preconditions("WARP_SPEED", state)
    assert res_unknown.valid is False
    assert "Unknown action" in res_unknown.reason

    # 2. Degraded IMU fails SWITCH_TO_IMU_ONLY precondition
    corrupt_imu_state = state.model_copy(update={"imu_trust": 0.35})
    res_imu = validate_preconditions("SWITCH_TO_IMU_ONLY", corrupt_imu_state)
    assert res_imu.valid is False
    assert "sensor_imu_availability" in res_imu.reason or "IMU" in res_imu.reason

    # 3. Valid state passes preconditions
    res_valid = validate_preconditions("SWITCH_TO_IMU_ONLY", state)
    assert res_valid.valid is True
    assert len(res_valid.checks) >= 3
    assert all(c.passed for c in res_valid.checks)


# ==============================================================================
# 3. SIMULATION ENGINE ISOLATION
# ==============================================================================

def test_simulation_operates_on_clone_no_real_mutation(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=7.0)

    # Record real simulator state before simulation
    initial_time = sim.time
    initial_mode = sim.navigation_mode
    initial_x = sim.x
    initial_y = sim.y

    # Execute simulation
    sim_res = sim_engine.simulate("SWITCH_TO_IMU_ONLY")
    assert sim_res.success is True
    assert sim_res.action_id == "SWITCH_TO_IMU_ONLY"
    assert sim_res.predicted_risk < 0.50
    assert sim_res.mission_success_probability >= 0.90
    assert sim_res.estimated_delay == 18.0
    assert len(sim_res.affected_capabilities) > 0
    assert len(sim_res.side_effects) > 0

    # Invariant: Real simulator was NOT mutated
    assert sim.time == initial_time
    assert sim.navigation_mode == initial_mode
    assert sim.x == initial_x
    assert sim.y == initial_y

    # Counterfactual comparison
    comparisons = sim_engine.compare_actions()
    assert len(comparisons) == 3
    for c in comparisons:
        assert "action_id" in c
        assert "predicted_risk" in c
        assert "success_probability" in c
        assert "estimated_delay" in c


# ==============================================================================
# 4. POLICY GOVERNANCE & RISK TIERS
# ==============================================================================

def test_policy_risk_tiers_and_denials(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=8.0)
    state = sim.get_state()

    # Rule POL-01: Critical residual & trust below hard floor -> DENY
    pol_gps = policy.evaluate_policy("REQUEST_GPS_REACQUISITION", state)
    assert pol_gps.status == PolicyStatus.DENY
    assert pol_gps.allowed is False
    assert pol_gps.authorization_status == AuthorizationStatus.DENIED
    assert len(pol_gps.violations) > 0

    # Rule POL-02: Degraded inertial transition -> REQUIRES_HUMAN_AUTHORIZATION
    pol_imu = policy.evaluate_policy("SWITCH_TO_IMU_ONLY", state)
    assert pol_imu.status == PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION
    assert pol_imu.requires_authorization is True
    assert pol_imu.allowed is False
    assert pol_imu.authorization_status == AuthorizationStatus.PENDING

    # Rule POL-03: Failsafe safe mode -> ALLOW (NOT_REQUIRED)
    pol_safe = policy.evaluate_policy("ENTER_SAFE_MODE", state)
    assert pol_safe.status == PolicyStatus.ALLOW
    assert pol_safe.allowed is True
    assert pol_safe.authorization_status == AuthorizationStatus.NOT_REQUIRED


# ==============================================================================
# 5. AUTHORIZATION CONTROLS
# ==============================================================================

def test_authorization_enforcement(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=8.0)
    state = sim.get_state()

    assert not policy.is_authorized("SWITCH_TO_IMU_ONLY")

    # Authorizing unlocks the action
    policy.authorize_action("SWITCH_TO_IMU_ONLY")
    assert policy.is_authorized("SWITCH_TO_IMU_ONLY")

    pol_unlocked = policy.evaluate_policy("SWITCH_TO_IMU_ONLY", state)
    assert pol_unlocked.allowed is True
    assert pol_unlocked.authorization_status == AuthorizationStatus.APPROVED

    # Denying overrides authorization
    policy.deny_action("SWITCH_TO_IMU_ONLY")
    pol_denied = policy.evaluate_policy("SWITCH_TO_IMU_ONLY", state)
    assert pol_denied.allowed is False
    assert pol_denied.authorization_status == AuthorizationStatus.DENIED


# ==============================================================================
# 6. EXECUTION GATES & CONTAINMENT
# ==============================================================================

def test_execution_gates_prevent_unauthorized_execution(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=8.0)
    initial_mode = sim.navigation_mode

    # Gate 1: Non-existent action rejected
    res_fake = adapter.execute_action("FLY_TO_ORBIT")
    assert res_fake.status == "FAILED"
    assert res_fake.success is False
    assert "Gate 1 Rejected" in res_fake.message
    assert sim.navigation_mode == initial_mode

    # Gate 3: Policy DENIED rejected
    res_denied = adapter.execute_action("REQUEST_GPS_REACQUISITION")
    assert res_denied.status == "FAILED"
    assert "rejected by governance gate" in res_denied.message
    assert sim.navigation_mode == initial_mode

    # Gate 4: Policy PENDING rejected
    res_pending = adapter.execute_action("SWITCH_TO_IMU_ONLY")
    assert res_pending.status == "FAILED"
    assert "GOVERNANCE GATE" in res_pending.message
    assert sim.navigation_mode == initial_mode

    # Once authorized, Gate 6 permits state mutation
    policy.authorize_action("SWITCH_TO_IMU_ONLY")
    res_success = adapter.execute_action("SWITCH_TO_IMU_ONLY")
    assert res_success.status == "COMPLETED"
    assert res_success.success is True
    assert res_success.previous_mode == initial_mode
    assert res_success.new_mode == NavigationMode.INERTIAL
    assert sim.navigation_mode == NavigationMode.INERTIAL
    assert "navigation_mode" in res_success.state_changes


# ==============================================================================
# 7. VERIFICATION ENGINE & CONTROLLED INTENTIONAL FAILURE
# ==============================================================================

def test_intentional_verification_failure_and_checks(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault(initial_bias=7.0)

    policy.authorize_action("SWITCH_TO_IMU_ONLY")
    exec_res = adapter.execute_action("SWITCH_TO_IMU_ONLY")
    assert exec_res.success is True

    # 1. First verification attempt MUST fail deliberately
    ver_res = verifier.verify_action("SWITCH_TO_IMU_ONLY")
    assert ver_res.success is False
    assert ver_res.verified is False
    assert ver_res.status == "failed"
    assert ver_res.next_action_required is True

    # Structured checks validation
    assert len(ver_res.checks) >= 2
    check_names = [c["name"] for c in ver_res.checks]
    assert "navigation_mode" in check_names
    assert "navigation_confidence" in check_names

    # Navigation mode passed, but confidence failed
    mode_check = next(c for c in ver_res.checks if c["name"] == "navigation_mode")
    assert mode_check["passed"] is True
    assert mode_check["actual"] == "INERTIAL"

    conf_check = next(c for c in ver_res.checks if c["name"] == "navigation_confidence")
    assert conf_check["passed"] is False
    assert conf_check["actual"] == "0.61"
    assert "navigation_confidence" in ver_res.failed_checks


# ==============================================================================
# 8. DYNAMIC REPLANNING
# ==============================================================================

def test_dynamic_replanning_after_failure(system_setup):
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup
    sim.inject_gps_fault()

    # Trigger deliberate failure
    policy.authorize_action("SWITCH_TO_IMU_ONLY")
    adapter.execute_action("SWITCH_TO_IMU_ONLY")
    ver_res = verifier.verify_action("SWITCH_TO_IMU_ONLY")
    assert ver_res.verified is False

    # Replanning invocation
    replan_res = verifier.replan(
        previous_action="SWITCH_TO_IMU_ONLY",
        reason=ver_res.message,
    )
    assert replan_res["status"] == "replanned"
    assert replan_res["replan_count"] == 1
    assert replan_res["previous_action"] == "SWITCH_TO_IMU_ONLY"
    assert replan_res["recommended_action"] in ("ENTER_SAFE_MODE", "safe_mode")
    assert len(replan_res["alternative_actions"]) >= 1

    # Alternative actions do NOT include the failed action
    alt_ids = [a["id"] for a in replan_res["alternative_actions"]]
    assert "SWITCH_TO_IMU_ONLY" not in alt_ids
    assert "ENTER_SAFE_MODE" in alt_ids

    # Execute alternative action (SAFE_MODE)
    exec_safe = adapter.execute_action("ENTER_SAFE_MODE")
    assert exec_safe.success is True

    # Verification must succeed for SAFE_MODE
    ver_safe = verifier.verify_action("ENTER_SAFE_MODE")
    assert ver_safe.success is True
    assert ver_safe.verified is True
    assert ver_safe.status == "safe"
    assert ver_safe.next_action_required is False
    assert sim.navigation_mode == NavigationMode.SAFE_MODE


# ==============================================================================
# 9. END-TO-END CANONICAL GPS INCIDENT LIFECYCLE
# ==============================================================================

def test_canonical_incident_repeatable_workflow(system_setup):
    """
    Demonstrates the complete canonical flow deterministically:
    NORMAL -> GPS degradation -> Evidence/Hypotheses/Impact ->
    Candidate actions -> Simulation -> Policy Gate (HITL Required) ->
    Authorization -> Execute -> Verification FAIL -> Replan ->
    Execute SAFE_MODE -> Verification SUCCESS -> RECOVERED.
    """
    sim, policy, sim_engine, adapter, verifier, context, registry = system_setup

    for iteration in range(2):
        # 1. Reset
        sim.reset(seed=42 + iteration)
        policy.reset_authorizations()
        verifier.reset()
        sim_engine.reset()

        # 2. Inject fault
        sim.inject_gps_fault(initial_bias=7.5)
        sim.tick()
        state = sim.get_state()
        assert state.gps_fault_active is True
        assert state.residual > 4.0

        # 3. Actions & Simulations
        actions = generate_actions(state)
        assert len(actions) == 3

        sim_switch = sim_engine.simulate("SWITCH_TO_IMU_ONLY")
        assert sim_switch.success is True

        # 4. Policy Gate
        pol_eval = policy.evaluate_policy("SWITCH_TO_IMU_ONLY", state)
        assert pol_eval.requires_authorization is True

        # 5. Authorize
        policy.authorize_action("SWITCH_TO_IMU_ONLY")

        # 6. Execute
        exec_1 = adapter.execute_action("SWITCH_TO_IMU_ONLY")
        assert exec_1.success is True
        assert sim.navigation_mode == NavigationMode.INERTIAL

        # 7. Verification Failure (Controlled Demo)
        ver_1 = verifier.verify_action("SWITCH_TO_IMU_ONLY")
        assert ver_1.verified is False

        # 8. Replan
        replan_out = verifier.replan(previous_action="SWITCH_TO_IMU_ONLY", reason=ver_1.message)
        assert replan_out["recommended_action"] in ("ENTER_SAFE_MODE", "safe_mode")

        # 9. Execute alternative
        exec_2 = adapter.execute_action("ENTER_SAFE_MODE")
        assert exec_2.success is True
        assert sim.navigation_mode == NavigationMode.SAFE_MODE

        # 10. Verify recovery
        ver_2 = verifier.verify_action("ENTER_SAFE_MODE")
        assert ver_2.verified is True
        assert ver_2.next_action_required is False


# ==============================================================================
# 10. REST API ENDPOINTS & HTTP GOVERNANCE
# ==============================================================================

def test_phase3_rest_api_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    client.post("/api/v1/reset")
    client.post("/api/v1/scenario/gps-integrity", json={"bias": 7.5})

    # 1. GET /api/v1/actions
    res_actions = client.get("/api/v1/actions")
    assert res_actions.status_code == 200
    act_data = res_actions.json()
    assert "actions" in act_data
    assert len(act_data["actions"]) == 3

    # 2. GET /api/v1/actions/compare
    res_cmp = client.get("/api/v1/actions/compare")
    assert res_cmp.status_code == 200
    cmp_data = res_cmp.json()
    assert "comparisons" in cmp_data
    assert len(cmp_data["comparisons"]) == 3

    # 3. POST /api/v1/actions/{action_id}/simulate
    res_sim = client.post("/api/v1/actions/SWITCH_TO_IMU_ONLY/simulate")
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["action_id"] == "SWITCH_TO_IMU_ONLY"
    assert sim_data["success"] is True
    assert "predicted_risk" in sim_data
    assert sim_data["estimated_delay"] == 18.0

    # 4. Attempt to execute without authorization must fail
    res_exec_unauth = client.post("/api/v1/actions/SWITCH_TO_IMU_ONLY/execute")
    assert res_exec_unauth.status_code == 200
    exec_unauth_data = res_exec_unauth.json()
    assert exec_unauth_data["status"] == "FAILED"
    assert exec_unauth_data["success"] is False

    # 5. POST /api/v1/authorization/{action_id} (Requirement 8)
    res_auth = client.post("/api/v1/authorization/SWITCH_TO_IMU_ONLY", json={"decision": "approve"})
    assert res_auth.status_code == 200
    auth_data = res_auth.json()
    assert auth_data["authorization_status"] == "APPROVED"

    # 6. POST /api/v1/actions/{action_id}/execute (Authorized execution)
    res_exec = client.post("/api/v1/actions/SWITCH_TO_IMU_ONLY/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["success"] is True
    assert exec_data["new_mode"] == "INERTIAL"

    # 7. POST /api/v1/actions/{action_id}/verify (Intentional Failure Demo)
    res_ver = client.post("/api/v1/actions/SWITCH_TO_IMU_ONLY/verify")
    assert res_ver.status_code == 200
    ver_data = res_ver.json()
    assert ver_data["verified"] is False
    assert len(ver_data["checks"]) >= 2
    assert "navigation_confidence" in ver_data["failed_checks"]

    # 8. Execute replacement failsafe (ENTER_SAFE_MODE)
    res_safe_exec = client.post("/api/v1/actions/ENTER_SAFE_MODE/execute")
    assert res_safe_exec.status_code == 200
    assert res_safe_exec.json()["success"] is True

    # 9. Verify SAFE_MODE -> Success
    res_safe_ver = client.post("/api/v1/actions/ENTER_SAFE_MODE/verify")
    assert res_safe_ver.status_code == 200
    assert res_safe_ver.json()["verified"] is True


def test_api_rejects_authorization_of_denied_or_unknown_actions():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    client.post("/api/v1/reset")
    client.post("/api/v1/scenario/gps-integrity", json={"bias": 9.0})

    # Unknown action returns 404
    res_unknown = client.post("/api/v1/authorization/WARP_DRIVE", json={"decision": "approve"})
    assert res_unknown.status_code == 404

    # Critical policy DENIED action cannot be authorized (returns 400)
    res_denied = client.post("/api/v1/authorization/REQUEST_GPS_REACQUISITION", json={"decision": "approve"})
    assert res_denied.status_code == 400
    assert "denied by governance policy" in res_denied.json()["detail"].lower()

