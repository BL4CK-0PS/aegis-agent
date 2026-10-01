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
