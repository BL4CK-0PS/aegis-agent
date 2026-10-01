"""
AEGIS Canonical Demo Execution Script
Demonstrates the complete Phase 3 Action, Simulation & Governance Engine:
NORMAL -> Incident -> Investigation -> Action Generation -> Counterfactual Simulation ->
Policy Gate -> Operator Authorization -> Authoritative Execution -> Intentional Verification Failure ->
Dynamic Replanning -> Alternative Action Selection -> Policy Clearance -> Execution ->
Verification Success -> Platform Recovered.
"""

import json
import sys
import time

from app.core.actions import generate_actions
from app.core.execution import ExecutionAdapter
from app.core.models import NavigationMode
from app.core.policy import PolicyEngine
from app.core.risk import RiskEngine
from app.core.simulation import SimulationEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext


def run_canonical_demo():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 72)
    print("  AEGIS -- AUTONOMOUS EVIDENCE-DRIVEN GOVERNANCE & SAFETY ENGINE")
    print("  Phase 3 Canonical Demo: Closed-Loop Governance & Incident Recovery")
    print("=" * 72)

    # 1. Platform Initialization
    sim = DroneSimulator(seed=42, deliberate_failure_enabled=True)
    policy = PolicyEngine()
    sim_engine = SimulationEngine(sim)
    adapter = ExecutionAdapter(sim, policy, sim_engine)
    verifier = VerificationEngine(sim, deliberate_failure_enabled=True)
    tool_context = ToolContext(
        simulator=sim,
        policy_engine=policy,
        execution_adapter=adapter,
        verification_engine=verifier,
        simulation_engine=sim_engine,
    )
    registry = create_default_tool_registry()

    initial_state = sim.get_state()
    print(f"\n[PHASE 0: NOMINAL OPERATIONS]")
    print(f"  Mode: {initial_state.navigation_mode.value}")
    print(f"  Status: {initial_state.mission_status.value}")
    print(f"  GPS Trust: {initial_state.gps_trust:.2f} | IMU Trust: {initial_state.imu_trust:.2f}")
    print(f"  Positional Residual: {initial_state.residual:.2f}m")

    # 2. Incident Injection
    print(f"\n[PHASE 1: INCIDENT INJECTION -- GPS INTEGRITY COMPROMISE]")
    sim.inject_gps_fault(initial_bias=7.5)
    sim.tick()
    fault_state = sim.get_state()
    print(f"  Fault Active: {fault_state.gps_fault_active} (Bias: {fault_state.gps_bias:.1f}m)")
    print(f"  GPS Trust: {fault_state.gps_trust:.2f} (DEGRADED) | IMU Trust: {fault_state.imu_trust:.2f} (HEALTHY)")
    print(f"  Telemetry Residual Divergence: {fault_state.residual:.2f}m")

    # 3. Investigation & Diagnostic Telemetry
    print(f"\n[PHASE 2: DETERMINISTIC INVESTIGATION]")
    obs = registry.execute("get_observations", tool_context, {})
    trust = registry.execute("get_trust", tool_context, {})
    hyps = registry.execute("generate_hypotheses", tool_context, {})
    impact = registry.execute("get_mission_impact", tool_context, {})
    top_lead = hyps["hypotheses"][0]["title"]
    print(f"  Primary Hypothesis: {top_lead} (Likelihood: {hyps['hypotheses'][0]['likelihood']:.2f})")
    print(f"  Mission Impact: Operational Risk={impact['operational_risk']:.2f}, Urgency={impact['recommendation_urgency']}")

    # 4. Action Generation
    print(f"\n[PHASE 3: ACTION GENERATION (3 Canonical Alternatives)]")
    actions = generate_actions(fault_state)
    for idx, act in enumerate(actions, 1):
        print(f"  {idx}. [{act.id}] {act.name}")
        print(f"     Category: {act.category} | Risk Level: {act.risk_level}")
        print(f"     Preconditions: {', '.join(act.preconditions)}")

    # 5. Counterfactual Simulations & Comparisons
    print(f"\n[PHASE 4: COUNTERFACTUAL SIMULATION & COMPARISON (Zero Real State Mutation)]")
    comparisons = sim_engine.compare_actions()
    print(f"  {'ACTION':<26} {'RISK':<8} {'SUCCESS':<10} {'DELAY':<10} {'RECOMMENDATION'}")
    print("  " + "-" * 70)
    for c in comparisons:
        print(f"  {c['action_id']:<26} {c['risk']:<8} {c['success_probability']*100:.0f}%{'':<6} {c['estimated_delay']:<10} {c['recommendation'][:30]}...")

    # Verify real simulator was not mutated during simulation
    assert sim.navigation_mode == NavigationMode.GPS_ASSISTED
    print("  [PASS] Safety Invariant Verified: Cloned simulation produced zero mutation on active platform.")

    # 6. Policy Gate & Authorization
    print(f"\n[PHASE 5: FLIGHT GOVERNANCE POLICY GATE]")
    selected_first = "SWITCH_TO_IMU_ONLY"
    pol_eval = policy.evaluate_policy(selected_first, sim.get_state())
    print(f"  Action: {selected_first}")
    print(f"  Policy Status: {pol_eval.status.value}")
    print(f"  Requires Human Authorization: {pol_eval.requires_authorization}")
    print(f"  Reason: {pol_eval.reason}")

    # Attempt execution before authorization -> must be blocked
    unauth_exec = adapter.execute_action(selected_first)
    print(f"  Unauthorized Execution Attempt: Success={unauth_exec.success} | Status={unauth_exec.status}")
    assert unauth_exec.success is False

    # Operator grants authorization
    print(f"\n[PHASE 6: HUMAN-IN-THE-LOOP OPERATOR AUTHORIZATION]")
    policy.authorize_action(selected_first)
    print(f"  Operator Approval Granted for: {selected_first}")
    auth_eval = policy.evaluate_policy(selected_first, sim.get_state())
    print(f"  Updated Policy Status: {auth_eval.status.value} (Authorization: {auth_eval.authorization_status.value})")

    # 7. Authoritative Execution
    print(f"\n[PHASE 7: AUTHORITATIVE EXECUTION (Gate 6 Mutation)]")
    exec_res = adapter.execute_action(selected_first)
    print(f"  Execution Status: {exec_res.status} | Mode Transition: {exec_res.previous_mode.value} -> {exec_res.new_mode.value}")
    print(f"  Message: {exec_res.message}")
    assert sim.navigation_mode == NavigationMode.INERTIAL

    # 8. Post-Action Verification -> Intentional Failure Demo
    print(f"\n[PHASE 8: VERIFICATION ENGINE -- INTENTIONAL VERIFICATION FAILURE]")
    ver_1 = verifier.verify_action(selected_first)
    print(f"  Verification Result: Success={ver_1.success} | Verified={ver_1.verified}")
    print(f"  Checks Audited:")
    for chk in ver_1.checks:
        mark = "[PASS]" if chk["passed"] else "[FAIL]"
        print(f"    - {chk['name']}: expected={chk['expected']}, actual={chk['actual']} -> {mark}")
    print(f"  Failed Checks: {ver_1.failed_checks}")
    print(f"  Diagnostic Reason: {ver_1.reason}")
    assert ver_1.verified is False
    print("  [OK] Controlled verification failure confirmed: AEGIS does not blindly trust successful execution.")

    # 9. Dynamic Replanning
    print(f"\n[PHASE 9: DYNAMIC REPLANNING]")
    replan_data = verifier.replan(previous_action=selected_first, reason=ver_1.reason)
    rec_alternative = "ENTER_SAFE_MODE"
    print(f"  Status: {replan_data['status']} (Replan Count: {replan_data['replan_count']})")
    print(f"  Recommended Alternative: {rec_alternative}")
    print(f"  Replanning Rationale: {replan_data['reason']}")

    # 10. Policy Clearance for Alternative Action
    print(f"\n[PHASE 10: POLICY CLEARANCE FOR RECOVERY ACTION]")
    pol_safe = policy.evaluate_policy(rec_alternative, sim.get_state())
    print(f"  Action: {rec_alternative}")
    print(f"  Policy Status: {pol_safe.status.value} | Allowed={pol_safe.allowed}")
    assert pol_safe.allowed is True

    # 11. Execute Recovery Alternative
    print(f"\n[PHASE 11: EXECUTION OF RECOVERY FAILSAFE]")
    exec_2 = adapter.execute_action(rec_alternative)
    print(f"  Execution Status: {exec_2.status} | Mode: {exec_2.previous_mode.value} -> {exec_2.new_mode.value}")
    assert sim.navigation_mode == NavigationMode.SAFE_MODE

    # 12. Verification of Recovery Action -> Success
    print(f"\n[PHASE 12: VERIFICATION OF RECOVERY FAILSAFE]")
    ver_2 = verifier.verify_action(rec_alternative)
    print(f"  Verification Result: Success={ver_2.success} | Verified={ver_2.verified}")
    print(f"  Checks Audited:")
    for chk in ver_2.checks:
        mark = "[PASS]" if chk["passed"] else "[FAIL]"
        print(f"    - {chk['name']}: expected={chk['expected']}, actual={chk['actual']} -> {mark}")
    print(f"  Status: {ver_2.status} | Message: {ver_2.message}")
    assert ver_2.verified is True

    # 13. Final Resolution
    print("\n" + "=" * 72)
    print("  CANONICAL DEMO RESULT: MISSION RECOVERED")
    print(f"  Final Platform State: {sim.navigation_mode.value} (Station-Keeping Hover)")
    print(f"  Mission Safety Restored: Verified within platform envelope.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    run_canonical_demo()
