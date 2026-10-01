"""
AEGIS Demo Orchestrator
Coordinates the canonical end-to-end incident recovery workflow:
ONE BUTTON -> COMPLETE AEGIS DECISION LOOP

Coordinates:
Observe -> Investigate -> Evidence -> Hypotheses -> Mission Impact ->
Generate Actions -> Simulate Actions -> Compare Outcomes -> Policy Evaluation ->
Authorization -> Execute -> Verify (Intentional Failure) -> Replan ->
Execute Replacement -> Verify (Success) -> Recovery.
"""

from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.core.actions import generate_actions, normalize_action_id
from app.core.execution import ExecutionAdapter
from app.core.models import NavigationMode, SystemState
from app.core.policy import PolicyEngine
from app.core.simulation import SimulationEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.demo.scenario import CANONICAL_SCENARIO, ScenarioDefinition
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry

logger = logging.getLogger("aegis.demo")


class DemoPhase(str, Enum):
    IDLE = "IDLE"
    INCIDENT = "INCIDENT"
    INVESTIGATING = "INVESTIGATING"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    SIMULATING = "SIMULATING"
    POLICY_CHECK = "POLICY_CHECK"
    AUTHORIZATION = "AUTHORIZATION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    REPLANNING = "REPLANNING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DemoTraceStep(BaseModel):
    step_id: str
    sequence: int
    phase: str
    tool: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    started_at: float
    completed_at: float
    summary: str
    result: Optional[Dict[str, Any]] = None


class DemoEvent(BaseModel):
    event: str
    phase: str
    timestamp: float
    demo_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class DemoResult(BaseModel):
    demo_id: str
    status: str  # COMPLETED, FAILED
    agent_mode: str  # "llm" or "deterministic_fallback"
    started_at: float
    completed_at: float
    duration_seconds: float
    incident: Dict[str, Any]
    investigation: Dict[str, Any]
    hypotheses: List[Dict[str, Any]]
    mission_impact: Dict[str, Any]
    dependency_graph: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]]
    selected_action: Optional[str] = None
    simulation: Dict[str, Any]
    policy: Dict[str, Any]
    execution: Dict[str, Any]
    verification: Dict[str, Any]
    replanning: Dict[str, Any]
    recovery: Dict[str, Any]
    final_state: Dict[str, Any]
    trace: List[Dict[str, Any]]


class DemoOrchestrator:
    """
    Deterministic End-to-End Orchestrator.
    Binds the authoritative platform engines into a single automated decision loop.
    Enforces the explicit DemoPhase lifecycle and provides an audit trace of every step.
    """

    def __init__(
        self,
        simulator: DroneSimulator,
        policy_engine: PolicyEngine,
        execution_adapter: ExecutionAdapter,
        verification_engine: VerificationEngine,
        simulation_engine: SimulationEngine,
        tool_registry: ToolRegistry,
        tool_context: ToolContext,
        scenario: Optional[ScenarioDefinition] = None,
    ):
        self.simulator = simulator
        self.policy_engine = policy_engine
        self.execution_adapter = execution_adapter
        self.verification_engine = verification_engine
        self.simulation_engine = simulation_engine
        self.registry = tool_registry
        self.context = tool_context
        self.scenario = scenario or CANONICAL_SCENARIO

        self.current_phase: DemoPhase = DemoPhase.IDLE
        self.current_demo_id: Optional[str] = None
        self.trace: List[DemoTraceStep] = []
        self.events: List[DemoEvent] = []
        self._active_connections: Set[Any] = set()
        self._last_result: Optional[DemoResult] = None

    def register_connection(self, websocket: Any) -> None:
        self._active_connections.add(websocket)

    def unregister_connection(self, websocket: Any) -> None:
        self._active_connections.discard(websocket)

    def _broadcast_event(self, event: DemoEvent) -> None:
        """Appends event and broadcasts asynchronously to connected subscribers."""
        self.events.append(event)
        event_dict = event.model_dump()

        dead_connections = []
        for ws in list(self._active_connections):
            try:
                # If in an active async event loop, schedule send
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass

                if loop and loop.is_running():
                    asyncio.create_task(ws.send_text(json.dumps(event_dict)))
                else:
                    asyncio.run(ws.send_text(json.dumps(event_dict)))
            except Exception:
                dead_connections.append(ws)

        for dead in dead_connections:
            self.unregister_connection(dead)

    def _log_event(
        self,
        phase: DemoPhase,
        event_name: str,
        action_id: Optional[str] = None,
        status: str = "COMPLETED",
    ) -> None:
        """Structured observability logging with no secrets or raw transcripts."""
        logger.info(
            "[DEMO_EVENT] demo_id=%s phase=%s event=%s action_id=%s status=%s timestamp=%.2f",
            self.current_demo_id,
            phase.value,
            event_name,
            action_id or "N/A",
            status,
            time.time(),
        )

    def emit_event(
        self,
        event_name: str,
        phase: DemoPhase,
        payload: Dict[str, Any],
        on_event: Optional[Callable[[DemoEvent], None]] = None,
    ) -> DemoEvent:
        event = DemoEvent(
            event=event_name,
            phase=phase.value,
            timestamp=time.time(),
            demo_id=self.current_demo_id or "DEMO-INIT",
            payload=payload,
        )
        self._broadcast_event(event)
        if on_event:
            try:
                on_event(event)
            except Exception as ex:
                logger.warning(f"Error in on_event callback: {ex}")
        return event

    def reset(self) -> Dict[str, Any]:
        """Resets simulator and orchestrator to clean nominal baseline."""
        self.simulator.reset(seed=self.scenario.seed)
        self.policy_engine.reset_authorizations()
        self.verification_engine.reset()
        self.simulation_engine.reset()
        self.current_phase = DemoPhase.IDLE
        self.trace.clear()
        self.events.clear()
        self._last_result = None

        nominal_state = self.simulator.get_state()
        return {
            "status": "reset_success",
            "phase": self.current_phase.value,
            "state": nominal_state.model_dump(),
        }

    def run(
        self,
        auto_authorize: bool = True,
        on_event: Optional[Callable[[DemoEvent], None]] = None,
    ) -> DemoResult:
        """
        Executes the entire deterministic incident response loop.
        ONE BUTTON -> COMPLETE AEGIS DECISION LOOP.
        """
        demo_id = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
        self.current_demo_id = demo_id
        agent_id = f"agent-{uuid.uuid4().hex[:6]}"
        started_at = time.time()
        self.trace.clear()
        sequence = 0

        # Determine agent mode
        agent_mode = "deterministic_fallback"

        def add_trace(
            tool_name: str,
            phase_val: DemoPhase,
            summary_text: str,
            result_data: Optional[Dict[str, Any]] = None,
            status_val: str = "COMPLETED",
        ) -> DemoTraceStep:
            nonlocal sequence
            sequence += 1
            step = DemoTraceStep(
                step_id=f"step-{sequence:02d}",
                sequence=sequence,
                phase=phase_val.value,
                tool=tool_name,
                status=status_val,
                started_at=time.time(),
                completed_at=time.time(),
                summary=summary_text,
                result=result_data,
            )
            self.trace.append(step)
            return step

        # ======================================================================
        # 1. RESET TO NOMINAL
        # ======================================================================
        self.current_phase = DemoPhase.IDLE
        self.reset()
        self.current_demo_id = demo_id
        self._log_event(self.current_phase, "demo_started")
        self.emit_event(
            "demo_started",
            self.current_phase,
            {"demo_id": demo_id, "scenario": self.scenario.name, "mode": agent_mode},
            on_event,
        )

        initial_state = self.simulator.get_state()
        self.emit_event("state_updated", self.current_phase, initial_state.model_dump(), on_event)

        # ======================================================================
        # 2. INJECT CANONICAL INCIDENT
        # ======================================================================
        self.current_phase = DemoPhase.INCIDENT
        self._log_event(self.current_phase, "incident_injected")
        self.simulator.inject_gps_fault(initial_bias=self.scenario.initial_bias)
        fault_state = self.simulator.tick()

        add_trace(
            tool_name="inject_gps_fault",
            phase_val=self.current_phase,
            summary_text=(
                f"GPS integrity fault injected (bias={self.scenario.initial_bias:.1f}m). "
                f"Positional residual divergence: {fault_state.residual:.2f}m."
            ),
            result_data={"residual": fault_state.residual, "bias": fault_state.gps_bias},
        )
        self.emit_event(
            "incident_injected",
            self.current_phase,
            {
                "type": "GPS_INTEGRITY_DEGRADATION",
                "bias": fault_state.gps_bias,
                "residual": fault_state.residual,
            },
            on_event,
        )
        self.emit_event("state_updated", self.current_phase, fault_state.model_dump(), on_event)

        # ======================================================================
        # 3. INVESTIGATION (Telemetry & Trust Diagnostics)
        # ======================================================================
        self.current_phase = DemoPhase.INVESTIGATING
        self._log_event(self.current_phase, "investigation_started")
        self.emit_event("agent_step_started", self.current_phase, {"step": "investigation"}, on_event)

        # 3a. get_system_state
        state_data = self.registry.execute("get_system_state", self.context, {})
        add_trace(
            "get_system_state",
            self.current_phase,
            f"Retrieved drone telemetry: mode={state_data.get('navigation_mode')}, status={state_data.get('mission_status')}.",
            state_data,
        )

        # 3b. get_observations
        obs_data = self.registry.execute("get_observations", self.context, {})
        add_trace(
            "get_observations",
            self.current_phase,
            f"Observed sensor divergence: residual={obs_data.get('residual'):.1f}m, anomaly_score={obs_data.get('anomaly_score'):.2f}.",
            obs_data,
        )

        # 3c. get_trust
        trust_data = self.registry.execute("get_trust", self.context, {})
        add_trace(
            "get_trust",
            self.current_phase,
            f"Calibrated statistical trust: GPS={trust_data.get('gps_trust'):.2f}, IMU={trust_data.get('imu_trust'):.2f}.",
            trust_data,
        )
        self.emit_event("trust_updated", self.current_phase, trust_data, on_event)

        # ======================================================================
        # 4. ANALYSIS (Hypotheses, Impact, and Dependency Graph)
        # ======================================================================
        self.current_phase = DemoPhase.ANALYZING
        self._log_event(self.current_phase, "analysis_started")

        # 4a. generate_hypotheses
        hyps_data = self.registry.execute("generate_hypotheses", self.context, {})
        top_hyp = hyps_data.get("hypotheses", [{}])[0].get("title", "Unknown")
        add_trace(
            "generate_hypotheses",
            self.current_phase,
            f"Synthesized competing hypotheses. Primary lead: {top_hyp}.",
            hyps_data,
        )
        self.emit_event("hypotheses_updated", self.current_phase, hyps_data, on_event)

        # 4b. get_mission_impact
        impact_data = self.registry.execute("get_mission_impact", self.context, {})
        add_trace(
            "get_mission_impact",
            self.current_phase,
            f"Evaluated mission impact: risk={impact_data.get('operational_risk'):.2f}, urgency={impact_data.get('recommendation_urgency')}.",
            impact_data,
        )
        self.emit_event("impact_updated", self.current_phase, impact_data, on_event)

        # 4c. get_dependency_graph
        graph_data = self.registry.execute("get_dependency_graph", self.context, {})
        add_trace(
            "get_dependency_graph",
            self.current_phase,
            f"Mapped subsystem dependency graph ({len(graph_data.get('nodes', []))} nodes).",
            graph_data,
        )

        # ======================================================================
        # 5. PLANNING (Candidate Action Generation)
        # ======================================================================
        self.current_phase = DemoPhase.PLANNING
        self._log_event(self.current_phase, "planning_started")

        actions_data = self.registry.execute("generate_actions", self.context, {})
        cands = actions_data.get("actions", [])
        add_trace(
            "generate_actions",
            self.current_phase,
            f"Generated {len(cands)} candidate response actions tailored to degraded navigation state.",
            actions_data,
        )
        self.emit_event("actions_generated", self.current_phase, actions_data, on_event)

        # ======================================================================
        # 6. SIMULATION & COMPARISON (Counterfactuals on Cloned State)
        # ======================================================================
        self.current_phase = DemoPhase.SIMULATING
        self._log_event(self.current_phase, "simulation_started")

        # Simulate candidate 1: SWITCH_TO_IMU_ONLY
        sim_1 = self.registry.execute("simulate_action", self.context, {"action": "SWITCH_TO_IMU_ONLY"})
        add_trace(
            "simulate_action",
            self.current_phase,
            f"Simulated 'SWITCH_TO_IMU_ONLY': Predicted Risk={sim_1.get('predicted_risk'):.2f}, Delay={sim_1.get('estimated_delay'):.0f}s.",
            sim_1,
        )

        # Simulate candidate 2: REQUEST_GPS_REACQUISITION
        sim_2 = self.registry.execute("simulate_action", self.context, {"action": "REQUEST_GPS_REACQUISITION"})
        add_trace(
            "simulate_action",
            self.current_phase,
            f"Simulated 'REQUEST_GPS_REACQUISITION': Predicted Risk={sim_2.get('predicted_risk'):.2f}, Continuity={sim_2.get('mission_continuity'):.2f}.",
            sim_2,
        )

        # Comparative evaluation
        comparisons = self.simulation_engine.compare_actions()
        self.emit_event("simulation_completed", self.current_phase, {"comparisons": comparisons}, on_event)

        # Selection of primary candidate
        selected_action_1 = "SWITCH_TO_IMU_ONLY"

        # ======================================================================
        # 7. POLICY GOVERNANCE CHECK (Rule POL-02 Gate)
        # ======================================================================
        self.current_phase = DemoPhase.POLICY_CHECK
        self._log_event(self.current_phase, "policy_evaluated", action_id=selected_action_1)

        pol_1 = self.registry.execute("evaluate_policy", self.context, {"action": selected_action_1})
        add_trace(
            "evaluate_policy",
            self.current_phase,
            f"Policy evaluation for '{selected_action_1}': {pol_1.get('status')} (Requires Auth: {pol_1.get('requires_authorization')}).",
            pol_1,
        )
        self.emit_event("policy_evaluated", self.current_phase, pol_1, on_event)

        # ======================================================================
        # 8. AUTHORIZATION GATE
        # ======================================================================
        if pol_1.get("requires_authorization"):
            self.current_phase = DemoPhase.AUTHORIZATION
            self._log_event(self.current_phase, "authorization_required", action_id=selected_action_1)
            self.emit_event(
                "authorization_required",
                self.current_phase,
                {"action_id": selected_action_1, "reason": pol_1.get("reason")},
                on_event,
            )

            if auto_authorize:
                self.policy_engine.authorize_action(selected_action_1)
                self._log_event(self.current_phase, "authorization_completed", action_id=selected_action_1)
                add_trace(
                    "request_authorization",
                    self.current_phase,
                    f"Operator granted Human-in-the-Loop authorization for '{selected_action_1}'.",
                    {"action_id": selected_action_1, "authorization_status": "APPROVED"},
                )
                self.emit_event(
                    "authorization_completed",
                    self.current_phase,
                    {"action_id": selected_action_1, "status": "APPROVED"},
                    on_event,
                )

        # ======================================================================
        # 9. EXECUTION (Attempt 1: SWITCH_TO_IMU_ONLY)
        # ======================================================================
        self.current_phase = DemoPhase.EXECUTING
        self._log_event(self.current_phase, "execution_started", action_id=selected_action_1)
        self.emit_event(
            "execution_started",
            self.current_phase,
            {"action_id": selected_action_1},
            on_event,
        )

        exec_1 = self.registry.execute("execute_action", self.context, {"action": selected_action_1})
        add_trace(
            "execute_action",
            self.current_phase,
            f"Authoritative execution of '{selected_action_1}': Status={exec_1.get('status')}, Mode={exec_1.get('new_mode')}.",
            exec_1,
        )
        self.emit_event("execution_completed", self.current_phase, exec_1, on_event)
        self.emit_event(
            "state_updated",
            self.current_phase,
            self.simulator.get_state().model_dump(),
            on_event,
        )

        # ======================================================================
        # 10. VERIFICATION (Attempt 1: Intentional Failure Demo)
        # ======================================================================
        self.current_phase = DemoPhase.VERIFYING
        self._log_event(self.current_phase, "verification_started", action_id=selected_action_1)
        self.emit_event(
            "verification_started",
            self.current_phase,
            {"action_id": selected_action_1},
            on_event,
        )

        ver_1 = self.registry.execute("verify_action", self.context, {"action": selected_action_1})
        assert not ver_1.get("verified", False), "Controlled verification failure expected on first attempt"

        add_trace(
            "verify_action",
            self.current_phase,
            f"Verification FAILED: {ver_1.get('reason')}",
            ver_1,
            status_val="FAILED",
        )
        self.emit_event(
            "verification_failed",
            self.current_phase,
            {
                "action_id": selected_action_1,
                "reason": ver_1.get("reason"),
                "failed_checks": ver_1.get("failed_checks"),
            },
            on_event,
        )

        # ======================================================================
        # 11. DYNAMIC REPLANNING (Triggered by Verification Failure)
        # ======================================================================
        self.current_phase = DemoPhase.REPLANNING
        self._log_event(self.current_phase, "replan_started")
        self.emit_event(
            "replan_started",
            self.current_phase,
            {"failed_action": selected_action_1, "reason": ver_1.get("reason")},
            on_event,
        )

        replan_res = self.registry.execute(
            "replan",
            self.context,
            {
                "previous_action": selected_action_1,
                "reason": ver_1.get("reason"),
            },
        )
        rec_action = replan_res.get("recommended_action", "ENTER_SAFE_MODE")
        add_trace(
            "replan",
            self.current_phase,
            f"Dynamic replanning triggered: Reassessed alternatives. Recommended recovery failsafe: '{rec_action}'.",
            replan_res,
        )
        self.emit_event("replan_completed", self.current_phase, replan_res, on_event)

        # ======================================================================
        # 12. RECOVERY ALTERNATIVE: SIMULATE & POLICY (Attempt 2: ENTER_SAFE_MODE)
        # ======================================================================
        self.current_phase = DemoPhase.SIMULATING
        sim_safe = self.registry.execute("simulate_action", self.context, {"action": rec_action})
        add_trace(
            "simulate_action",
            self.current_phase,
            f"Simulated recovery failsafe '{rec_action}': Predicted Risk={sim_safe.get('predicted_risk'):.2f}, Success={sim_safe.get('mission_success_probability')*100:.0f}%.",
            sim_safe,
        )

        self.current_phase = DemoPhase.POLICY_CHECK
        pol_safe = self.registry.execute("evaluate_policy", self.context, {"action": rec_action})
        add_trace(
            "evaluate_policy",
            self.current_phase,
            f"Policy evaluation for emergency failsafe '{rec_action}': {pol_safe.get('status')} (Allowed: {pol_safe.get('allowed')}).",
            pol_safe,
        )

        # ======================================================================
        # 13. RECOVERY EXECUTION (Attempt 2: ENTER_SAFE_MODE)
        # ======================================================================
        self.current_phase = DemoPhase.EXECUTING
        self._log_event(self.current_phase, "execution_started", action_id=rec_action)
        self.emit_event("execution_started", self.current_phase, {"action_id": rec_action}, on_event)

        exec_2 = self.registry.execute("execute_action", self.context, {"action": rec_action})
        add_trace(
            "execute_action",
            self.current_phase,
            f"Authoritative execution of recovery failsafe '{rec_action}': New Mode={exec_2.get('new_mode')}.",
            exec_2,
        )
        self.emit_event("execution_completed", self.current_phase, exec_2, on_event)
        self.emit_event(
            "state_updated",
            self.current_phase,
            self.simulator.get_state().model_dump(),
            on_event,
        )

        # ======================================================================
        # 14. VERIFICATION OF RECOVERY (Attempt 2: SUCCESS)
        # ======================================================================
        self.current_phase = DemoPhase.VERIFYING
        self._log_event(self.current_phase, "verification_started", action_id=rec_action)
        ver_2 = self.registry.execute("verify_action", self.context, {"action": rec_action})
        assert ver_2.get("verified", False), "Verification must succeed for recovery safe mode"

        add_trace(
            "verify_action",
            self.current_phase,
            f"Verification PASSED: {ver_2.get('reason')}",
            ver_2,
            status_val="COMPLETED",
        )
        self.emit_event(
            "verification_succeeded",
            self.current_phase,
            {"action_id": rec_action, "status": "safe", "reason": ver_2.get("reason")},
            on_event,
        )

        # ======================================================================
        # 15. RECOVERY CONCLUSION
        # ======================================================================
        self.current_phase = DemoPhase.RECOVERING
        final_state = self.simulator.get_state()
        self._log_event(self.current_phase, "recovery_stabilized")

        self.current_phase = DemoPhase.COMPLETED
        completed_at = time.time()
        self._log_event(self.current_phase, "demo_completed")

        demo_result = DemoResult(
            demo_id=demo_id,
            status="COMPLETED",
            agent_mode=agent_mode,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round(completed_at - started_at, 2),
            incident={
                "scenario_id": self.scenario.scenario_id,
                "name": self.scenario.name,
                "type": "GPS_INTEGRITY_DEGRADATION",
                "bias": fault_state.gps_bias,
                "initial_residual": fault_state.residual,
            },
            investigation={
                "telemetry": state_data,
                "observations": obs_data,
                "trust": trust_data,
            },
            hypotheses=hyps_data.get("hypotheses", []),
            mission_impact=impact_data,
            dependency_graph=graph_data,
            actions=cands,
            selected_action=rec_action,
            simulation={
                "primary": sim_1,
                "comparisons": comparisons,
                "recovery": sim_safe,
            },
            policy={
                "primary": pol_1,
                "recovery": pol_safe,
            },
            execution={
                "attempt_1": exec_1,
                "attempt_2": exec_2,
            },
            verification={
                "attempt_1_failure": ver_1,
                "attempt_2_success": ver_2,
            },
            replanning=replan_res,
            recovery={
                "final_mode": final_state.navigation_mode.value,
                "verified": True,
                "status": "RECOVERED",
                "summary": "Vehicle safely stabilized in station-keeping SAFE_MODE hover.",
            },
            final_state=final_state.model_dump(),
            trace=[s.model_dump() for s in self.trace],
        )

        self.emit_event("demo_completed", self.current_phase, demo_result.model_dump(), on_event)
        self._last_result = demo_result
        return demo_result

    def get_state(self) -> Dict[str, Any]:
        """Returns instantaneous demo state."""
        return {
            "demo_id": self.current_demo_id,
            "phase": self.current_phase.value,
            "completed": self.current_phase in (DemoPhase.COMPLETED, DemoPhase.FAILED),
            "simulator_state": self.simulator.get_state().model_dump(),
            "total_steps": len(self.trace),
            "replan_count": self.simulator.replan_count,
        }

    def get_trace(self) -> List[Dict[str, Any]]:
        """Returns complete structured trace history."""
        return [s.model_dump() for s in self.trace]

    def get_events(self) -> List[Dict[str, Any]]:
        """Returns complete event stream history."""
        return [e.model_dump() for e in self.events]
