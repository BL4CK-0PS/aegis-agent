"""
AEGIS LLM Agent Runtime
Implements bounded multi-turn tool-calling loop with schema validation,
tool-call budget enforcement, multi-tool-call handling, and sanitized audit tracing.
"""

from __future__ import annotations
import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agent.planner import AEGIS_SYSTEM_PROMPT
from app.agent.provider import LLMProvider, ProviderResponse, ToolCallItem, get_provider
from app.core.models import AgentEvent
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry

logger = logging.getLogger("aegis.llm_runtime")


def safe_json_serialize(obj: Any) -> Any:
    """Recursively converts Pydantic models, dataclasses, and Enums to JSON-safe primitives."""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_json_serialize(v) for v in obj]
    return obj


class LLMRunResult(BaseModel):
    agent_id: str
    incident_id: str
    status: str  # COMPLETED, BUDGET_EXCEEDED, ERROR
    goal: str
    rounds: int
    tool_calls_count: int
    trace: List[Dict[str, Any]]
    events: List[Dict[str, Any]] = Field(default_factory=list)
    completed: bool = True
    waiting_for_authorization: bool = False
    pending_action: Optional[str] = None
    replan_count: int = 0
    final_summary: str
    provider_used: str
    error: Optional[str] = None


class LLMRuntime:
    """
    Executes a bounded reasoning loop:
    Prompt -> Model Tool Selection -> Argument Validation -> Tool Execution -> Result -> Next Step.
    """

    READ_ONLY_INVESTIGATION_TOOLS = [
        "get_system_state",
        "get_observations",
        "get_trust",
        "generate_hypotheses",
        "get_mission_impact",
        "get_dependency_graph",
    ]

    def __init__(
        self,
        tool_registry: ToolRegistry,
        tool_context: ToolContext,
        provider: Optional[LLMProvider] = None,
        max_rounds: int = 8,
        max_tool_calls: int = 15,
        allowed_tools: Optional[List[str]] = None,
    ):
        self.registry = tool_registry
        self.context = tool_context
        self.provider = provider or get_provider()
        self.max_rounds = max_rounds
        self.max_tool_calls = max_tool_calls
        self.allowed_tools = allowed_tools or self.READ_ONLY_INVESTIGATION_TOOLS
        self._lock = threading.Lock()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns OpenAPI/JSON Schema function definitions for allowed tools."""
        schemas = []
        for name in self.allowed_tools:
            tool = self.registry.get(name)
            if tool:
                schemas.append(tool.to_function_definition())
        return schemas

    def run(
        self,
        incident_id: str = "INC-GPS-001",
        goal: str = "Investigate flight telemetry anomaly and determine sensor integrity.",
        provider_override: Optional[LLMProvider] = None,
    ) -> LLMRunResult:
        """
        Executes the LLM multi-turn investigation loop thread-safely with strict budgeting.
        """
        provider = provider_override or self.provider
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        with self._lock:
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": AEGIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Incident ID: {incident_id}\n"
                        f"Mission Goal: {goal}\n"
                        "Available tools are read-only investigation diagnostics. "
                        "Investigate the reported sensor anomaly, synthesize hypotheses, and conclude with findings."
                    ),
                },
            ]

            tools_schema = self.get_tool_schemas()
            trace: List[Dict[str, Any]] = []
            total_tool_calls = 0
            current_round = 0
            final_summary = ""

            def _build_result(status_code: str, summary_text: str, err_msg: Optional[str] = None) -> LLMRunResult:
                events_list = [
                    {
                        "step": t["step"],
                        "tool": t["tool"],
                        "status": t["status"],
                        "summary": t["summary"],
                        "details": t.get("result"),
                    }
                    for t in trace
                ]
                return LLMRunResult(
                    agent_id=agent_id,
                    incident_id=incident_id,
                    status=status_code,
                    goal=goal,
                    rounds=current_round,
                    tool_calls_count=total_tool_calls,
                    trace=trace,
                    events=events_list,
                    completed=status_code in ("COMPLETED", "BUDGET_EXCEEDED"),
                    waiting_for_authorization=False,
                    pending_action=None,
                    replan_count=0,
                    final_summary=summary_text,
                    provider_used=provider.__class__.__name__,
                    error=err_msg,
                )

            while current_round < self.max_rounds:
                current_round += 1

                try:
                    response: ProviderResponse = provider.chat(messages, tools_schema)
                except Exception as ex:
                    logger.error(f"Provider chat error: {ex}", exc_info=True)
                    return _build_result("ERROR", "Investigation aborted due to provider error.", err_msg=str(ex))

                # Check if model requested tool calls
                if response.has_tool_calls:
                    # Append assistant message with tool calls
                    assistant_msg: Dict[str, Any] = {
                        "role": "assistant",
                        "content": response.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": tc.raw_arguments or json.dumps(tc.arguments),
                                },
                            }
                            for tc in response.tool_calls
                        ],
                    }
                    messages.append(assistant_msg)

                    # Execute each tool call (supporting multiple tool calls per turn)
                    for tc in response.tool_calls:
                        total_tool_calls += 1
                        step_num = total_tool_calls

                        # 1. Budget enforcement
                        if total_tool_calls > self.max_tool_calls:
                            err_result = {
                                "success": False,
                                "error": f"Tool call budget exceeded (limit {self.max_tool_calls}).",
                            }
                            trace.append({
                                "step": step_num,
                                "tool": tc.name,
                                "arguments": tc.arguments,
                                "status": "budget_exceeded",
                                "summary": "Tool budget exceeded; invocation halted.",
                                "result": err_result,
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.name,
                                "content": json.dumps(err_result),
                            })
                            continue

                        # 2. Argument parse validation
                        if tc.parse_error:
                            err_result = {
                                "success": False,
                                "error": f"Invalid tool arguments: {tc.parse_error}",
                            }
                            trace.append({
                                "step": step_num,
                                "tool": tc.name,
                                "arguments": tc.arguments,
                                "status": "malformed_arguments",
                                "summary": f"Rejected malformed arguments for '{tc.name}'.",
                                "result": err_result,
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.name,
                                "content": json.dumps(err_result),
                            })
                            continue

                        # 3. Authorization check on allowed tools
                        if tc.name not in self.allowed_tools:
                            err_result = {
                                "success": False,
                                "error": (
                                    f"Tool '{tc.name}' is unauthorized or outside read-only investigation scope. "
                                    f"Allowed tools: {self.allowed_tools}"
                                ),
                            }
                            trace.append({
                                "step": step_num,
                                "tool": tc.name,
                                "arguments": tc.arguments,
                                "status": "unauthorized_tool",
                                "summary": f"Rejected unauthorized tool '{tc.name}'.",
                                "result": err_result,
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.name,
                                "content": json.dumps(err_result),
                            })
                            continue

                        # 4. Authoritative execution
                        raw_result = self.registry.execute(tc.name, self.context, tc.arguments)
                        clean_result = safe_json_serialize(raw_result)

                        summary = self._summarize_tool_execution(tc.name, clean_result)
                        trace.append({
                            "step": step_num,
                            "tool": tc.name,
                            "arguments": tc.arguments,
                            "status": "completed" if clean_result.get("success", True) is not False else "failed",
                            "summary": summary,
                            "result": clean_result,
                        })

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.name,
                            "content": json.dumps(clean_result),
                        })

                    # If budget was reached, conclude
                    if total_tool_calls >= self.max_tool_calls:
                        return _build_result("BUDGET_EXCEEDED", "Investigation concluded due to reaching step budget cap.")

                else:
                    # Model provided text conclusion without requesting additional tools
                    final_summary = response.content or "Investigation concluded."
                    messages.append({"role": "assistant", "content": final_summary})
                    return _build_result("COMPLETED", final_summary)

            # Reached max conversation rounds
            return _build_result("COMPLETED", final_summary or "Investigation completed maximum allowed turns.")

    def _summarize_tool_execution(self, tool_name: str, result: Dict[str, Any]) -> str:
        if tool_name == "get_system_state":
            mode = result.get("navigation_mode", "UNKNOWN")
            status = result.get("mission_status", "UNKNOWN")
            return f"Retrieved system state: mode={mode}, status={status}."
        elif tool_name == "get_observations":
            residual = result.get("residual", 0.0)
            score = result.get("anomaly_score", 0.0)
            return f"Sensor observations analyzed: residual={residual:.2f}m, anomaly_score={score:.3f}."
        elif tool_name == "get_trust":
            gps_t = result.get("gps_trust", 0.0)
            imu_t = result.get("imu_trust", 0.0)
            return f"Calculated trust indices: GPS={gps_t:.2f}, IMU={imu_t:.2f}."
        elif tool_name == "generate_hypotheses":
            hyps = result.get("hypotheses", [])
            lead = hyps[0].get("title", "Unknown") if hyps else "None"
            return f"Synthesized {len(hyps)} hypotheses. Primary lead: {lead}."
        elif tool_name == "get_mission_impact":
            risk = result.get("operational_risk", 0.0)
            urgency = result.get("recommendation_urgency", "NORMAL")
            return f"Evaluated mission impact: risk={risk:.2f}, urgency={urgency}."
        elif tool_name == "get_dependency_graph":
            nodes = result.get("nodes", [])
            return f"Constructed dependency graph with {len(nodes)} subsystem nodes."
        return f"Executed {tool_name}."
