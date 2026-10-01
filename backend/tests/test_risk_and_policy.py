"""
Tests for RiskEngine, PolicyEngine, and Actuator Boundaries
"""

import pytest
from app.core.execution import ExecutionAdapter
from app.core.models import MissionStatus, NavigationMode, PolicyStatus
from app.core.policy import PolicyEngine
from app.core.risk import RiskEngine
from app.core.simulator import DroneSimulator


def test_mission_impact_and_dependency_graph():
    sim = DroneSimulator(seed=42)
    sim.inject_gps_fault(initial_bias=7.0)
    for _ in range(2):
        sim.tick()

    state = sim.get_state()
    impact = RiskEngine.evaluate_mission_impact(state)

    assert impact.operational_risk > 0.70
    assert impact.mission_status in (MissionStatus.CRITICAL, MissionStatus.DEGRADED)
    assert len(impact.affected_capabilities) > 0
    assert impact.recommendation_urgency in ("HIGH", "IMMEDIATE")

    # Dependency graph
    graph = RiskEngine.get_dependency_graph(state)
    assert len(graph.nodes) >= 6
    assert len(graph.edges) >= 5

    gps_node = next(n for n in graph.nodes if n.id == "sensor_gps")
    assert gps_node.status in ("critical", "degraded")


def test_policy_governance_rules():
    sim = DroneSimulator(seed=42)
    policy = PolicyEngine()

    sim.inject_gps_fault(initial_bias=8.0)
    state = sim.get_state()

    # Rule 1: Continue GPS when degraded should be DENIED
    eval_gps = policy.evaluate_policy("continue_gps", state)
    assert eval_gps.status == PolicyStatus.DENY
    assert eval_gps.allowed is False
    assert "POLICY VIOLATION" in eval_gps.reason

    # Rule 2: Switch to Inertial requires human authorization
    eval_inertial = policy.evaluate_policy("switch_inertial", state)
    assert eval_inertial.status == PolicyStatus.REQUIRES_HUMAN_AUTHORIZATION
    assert eval_inertial.allowed is False
    assert eval_inertial.requires_authorization is True

    # Authorizing switch_inertial unlocks it
    policy.authorize_action("switch_inertial")
    eval_inertial_authorized = policy.evaluate_policy("switch_inertial", state)
    assert eval_inertial_authorized.status == PolicyStatus.ALLOW
    assert eval_inertial_authorized.allowed is True

    # Rule 3: Safe Mode is always allowed as failsafe
    eval_safe = policy.evaluate_policy("safe_mode", state)
    assert eval_safe.status == PolicyStatus.ALLOW
    assert eval_safe.allowed is True


def test_execution_adapter_safety_containment():
    sim = DroneSimulator(seed=42)
    policy = PolicyEngine()
    adapter = ExecutionAdapter(sim, policy)

    sim.inject_gps_fault(initial_bias=8.0)
    initial_mode = sim.navigation_mode

    # Attempting to execute unauthorized switch_inertial must be BLOCKED
    res_unauth = adapter.execute_action("switch_inertial")
    assert res_unauth.success is False
    assert "rejected by governance gate" in res_unauth.details.lower()
    assert sim.navigation_mode == initial_mode  # simulator must not mutate!

    # Attempting arbitrary/invalid action must be BLOCKED
    res_invalid = adapter.execute_action("fly_to_space")
    assert res_invalid.success is False
    assert sim.navigation_mode == initial_mode

    # Once authorized by human, execution succeeds
    policy.authorize_action("switch_inertial")
    res_auth = adapter.execute_action("switch_inertial")
    assert res_auth.success is True
    assert sim.navigation_mode == NavigationMode.INERTIAL
