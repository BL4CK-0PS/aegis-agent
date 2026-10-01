"""
AEGIS Tool Context
Provides state and engine references to tools at execution time.
"""

from __future__ import annotations
from dataclasses import dataclass
from app.core.execution import ExecutionAdapter
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine


@dataclass
class ToolContext:
    simulator: DroneSimulator
    policy_engine: PolicyEngine
    execution_adapter: ExecutionAdapter
    verification_engine: VerificationEngine
    simulation_engine: Optional[Any] = None

    def __post_init__(self):
        if self.simulation_engine is None:
            from app.core.simulation import SimulationEngine
            self.simulation_engine = SimulationEngine(self.simulator)
        if getattr(self.execution_adapter, "simulation_engine", None) is None:
            self.execution_adapter.simulation_engine = self.simulation_engine
