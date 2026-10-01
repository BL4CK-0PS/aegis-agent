"""
AEGIS Demo Package
Provides canonical demo orchestrator, scenario definitions, state machine, and event streaming.
"""

from app.demo.orchestrator import (
    DemoEvent,
    DemoOrchestrator,
    DemoPhase,
    DemoResult,
    DemoTraceStep,
)
from app.demo.scenario import CANONICAL_SCENARIO, ScenarioDefinition

__all__ = [
    "DemoEvent",
    "DemoOrchestrator",
    "DemoPhase",
    "DemoResult",
    "DemoTraceStep",
    "ScenarioDefinition",
    "CANONICAL_SCENARIO",
]
