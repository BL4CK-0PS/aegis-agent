"""
AEGIS Agent State
Tracks multi-step investigation, intermediate evidence, candidate actions,
verification outcomes, and audit trace.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.models import AgentEvent


class AgentState(BaseModel):
    """
    Encapsulates complete agent context, tool invocation history,
    and current execution phase.
    """
    incident_id: str = "INC-GPS-001"
    goal: str = (
        "Investigate navigation telemetry discrepancy, isolate compromised sensors, "
        "mitigate mission risk, and restore verified safe flight operations."
    )
    current_step: int = 0
    max_steps: int = 20
    completed: bool = False
    waiting_for_authorization: bool = False
    pending_action: Optional[str] = None
    policy_blocked: bool = False

    # Trace and history
    events: List[AgentEvent] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls_count: int = 0
    replan_count: int = 0

    # Decision artifacts
    last_action: Optional[str] = None
    last_execution_result: Optional[Dict[str, Any]] = None
    last_verification_result: Optional[Dict[str, Any]] = None
    final_summary: Optional[str] = None

    def add_event(self, tool: str, status: str, summary: str, details: Optional[Dict[str, Any]] = None) -> AgentEvent:
        event = AgentEvent(
            step=self.current_step,
            tool=tool,
            status=status,
            summary=summary,
            details=details,
        )
        self.events.append(event)
        return event
