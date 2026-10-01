"""
AEGIS Execution Adapter
Authoritative actuator boundary between agent decisions and simulated platform.
Enforces 6-gate safety validation before allowing any state mutation.
"""

from __future__ import annotations
import time
from typing import Any, Dict, Optional
from app.core.actions import is_valid_action, normalize_action_id, validate_preconditions
from app.core.models import ExecutionResult, NavigationMode, SystemState
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator


class ExecutionAdapter:
    """
    Authoritative actuator boundary.
    Guarantees that neither the LLM nor the frontend can directly mutate simulator state.
    State changes must satisfy all 6 sequential execution gates.
    """

    def __init__(
        self,
        simulator: DroneSimulator,
        policy_engine: PolicyEngine,
        simulation_engine: Optional[Any] = None,
    ):
        self.simulator = simulator
        self.policy_engine = policy_engine
        self.simulation_engine = simulation_engine

    def execute_action(self, action_id: str) -> ExecutionResult:
        state = self.simulator.get_state()
        canonical_id = normalize_action_id(action_id)

        # Gate 1: Verify action exists
        if not is_valid_action(action_id):
            return ExecutionResult(
                action_id=action_id,
                status="FAILED",
                success=False,
                started_at=state.time,
                completed_at=state.time,
                previous_mode=state.navigation_mode,
                new_mode=state.navigation_mode,
                state_changes={},
                message=f"Gate 1 Rejected: Action '{action_id}' does not exist in registry.",
                details=f"Gate 1 Rejected: Action '{action_id}' does not exist in registry.",
            )

        # Gate 2: Verify preconditions
        precond = validate_preconditions(action_id, state)
        if not precond.valid:
            return ExecutionResult(
                action_id=action_id,
                status="FAILED",
                success=False,
                started_at=state.time,
                completed_at=state.time,
                previous_mode=state.navigation_mode,
                new_mode=state.navigation_mode,
                state_changes={},
                message=f"Gate 2 Rejected: Precondition failure: {precond.reason}",
                details=f"Gate 2 Rejected: Precondition failure: {precond.reason}",
            )

        # Gate 3 & 4: Verify policy and authorization
        eval_result = self.policy_engine.evaluate_policy(action_id, state)
        if not eval_result.allowed:
            return ExecutionResult(
                action_id=action_id,
                status="FAILED",
                success=False,
                started_at=state.time,
                completed_at=state.time,
                previous_mode=state.navigation_mode,
                new_mode=state.navigation_mode,
                state_changes={},
                message=f"Execution rejected by governance gate: {eval_result.reason}",
                details=f"Execution rejected by governance gate: {eval_result.reason}",
            )

        # Gate 5: Verify action has a valid simulation
        if self.simulation_engine is not None:
            norm_key = action_id.lower().strip().replace("-", "_")
            sim = self.simulation_engine.simulated_actions.get(
                norm_key
            ) or self.simulation_engine.simulated_actions.get(canonical_id)
            if not sim:
                # Run deterministic counterfactual forecast to verify feasibility before mutating
                sim = self.simulation_engine.simulate(action_id, state)
            if not sim.success or sim.predicted_risk > 0.95:
                return ExecutionResult(
                    action_id=action_id,
                    status="FAILED",
                    success=False,
                    started_at=state.time,
                    completed_at=state.time,
                    previous_mode=state.navigation_mode,
                    new_mode=state.navigation_mode,
                    state_changes={},
                    message=f"Gate 5 Rejected: Simulation forecast failed ({sim.reason})",
                    details=f"Gate 5 Rejected: Simulation forecast failed ({sim.reason})",
                )

        # Gate 6: Mutate simulator state through authoritative interface
        started_at = self.simulator.time
        previous_mode = self.simulator.navigation_mode
        success, message = self.simulator.apply_action(action_id)
        completed_at = self.simulator.time
        current_mode = self.simulator.navigation_mode

        state_changes = {
            "navigation_mode": {
                "from": previous_mode.value,
                "to": current_mode.value,
            },
            "timestamp": completed_at,
        }

        return ExecutionResult(
            action_id=action_id,
            status="COMPLETED" if success else "FAILED",
            success=success,
            started_at=started_at,
            completed_at=completed_at,
            previous_mode=previous_mode,
            new_mode=current_mode,
            state_changes=state_changes,
            message=message,
            details=message,
        )
