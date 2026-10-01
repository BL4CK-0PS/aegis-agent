"""
AEGIS Execution Adapter
Safely applies approved, policy-validated actions to the drone simulator.
Prevents unvalidated or direct model mutations.
"""

from __future__ import annotations
import time
from app.core.models import ExecutionResult, NavigationMode, SystemState
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator


class ExecutionAdapter:
    """
    Authoritative actuator boundary between agent decisions and simulated platform.
    """

    def __init__(self, simulator: DroneSimulator, policy_engine: PolicyEngine):
        self.simulator = simulator
        self.policy_engine = policy_engine

    def execute_action(self, action_id: str) -> ExecutionResult:
        state = self.simulator.get_state()
        eval_result = self.policy_engine.evaluate_policy(action_id, state)

        if not eval_result.allowed:
            return ExecutionResult(
                action_id=action_id,
                success=False,
                timestamp=self.simulator.time,
                previous_mode=state.navigation_mode,
                new_mode=state.navigation_mode,
                details=f"Execution rejected by governance gate: {eval_result.reason}",
            )

        previous_mode = self.simulator.navigation_mode
        success, message = self.simulator.apply_action(action_id)
        current_mode = self.simulator.navigation_mode

        return ExecutionResult(
            action_id=action_id,
            success=success,
            timestamp=self.simulator.time,
            previous_mode=previous_mode,
            new_mode=current_mode,
            details=message,
        )
