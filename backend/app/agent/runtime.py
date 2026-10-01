"""
AEGIS Agent Runtime
Executes multi-step closed-loop investigation, enforcing tool contracts,
human-in-the-loop authorization gates, and maximum step safety limits.
"""

from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional
from app.agent.llm_provider import LLMProvider, LLMResponse, get_llm_provider
from app.agent.planner import create_initial_messages
from app.agent.state import AgentState
from app.core.models import AgentEvent
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry


class AgentRuntime:
    """
    Orchestrates the decision loop:
    Observe -> Investigate -> Evidence -> Hypotheses -> Trust -> Mission Impact ->
    Actions -> Simulation -> Policy -> Authorization -> Execute -> Verify -> Recover/Replan
    """

    MAX_STEPS = 20

    def __init__(
        self,
        tool_registry: ToolRegistry,
        tool_context: ToolContext,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.registry = tool_registry
        self.context = tool_context
        self.llm = llm_provider or get_llm_provider()
        self.state: Optional[AgentState] = None

    def start_investigation(
        self,
        incident_id: str = "INC-GPS-001",
        goal: str = "Investigate flight telemetry anomaly, isolate corrupted sensors, and recover safe flight operations.",
    ) -> AgentState:
        """Initializes a new agent investigation state."""
        self.state = AgentState(
            incident_id=incident_id,
            goal=goal,
            current_step=0,
            max_steps=self.MAX_STEPS,
            messages=create_initial_messages(goal, incident_id),
        )
        return self.state

    def investigate(
        self,
        incident_id: str = "INC-GPS-001",
        goal: str = "Investigate the navigation integrity incident.",
    ) -> AgentState:
        """
        Executes the Phase 1A deterministic 5-step diagnostic investigation:
        get_system_state -> get_observations -> get_trust -> generate_hypotheses -> get_mission_impact -> Conclusion.
        """
        self.start_investigation(incident_id=incident_id, goal=goal)
        state = self.state

        investigation_tools = [
            "get_system_state",
            "get_observations",
            "get_trust",
            "generate_hypotheses",
            "get_mission_impact",
        ]

        for tool_name in investigation_tools:
            state.current_step += 1
            result = self.registry.execute(tool_name, self.context, {})
            state.tool_calls_count += 1
            summary = self._create_summary_for_tool(tool_name, {}, result)
            state.add_event(
                tool=tool_name,
                status="completed" if result.get("success", True) is not False else "error",
                summary=summary,
                details=result,
            )

        state.completed = True
        state.final_summary = (
            "Diagnostic Investigation Complete: Telemetry observations confirm GPS signal integrity "
            "degradation (Hypothesis H1 selected as primary lead with highest confidence). "
            "Sensor trust degraded. Mission operational risk elevated."
        )
        return state

    def step(self, auto_authorize: bool = False) -> AgentState:
        """
        Advances the agent by a single step.
        """
        if not self.state:
            self.start_investigation()

        state = self.state
        if state.completed or state.current_step >= state.max_steps:
            state.completed = True
            return state

        state.current_step += 1
        tools_schema = self.registry.get_function_schemas()

        # Query LLM Provider
        response: LLMResponse = self.llm.chat(state.messages, tools_schema)

        if response.type == "tool_call" and response.tool_name:
            tool_name = response.tool_name
            tool_args = response.arguments or {}

            # Check if this tool requires human authorization prior to execution
            if tool_name == "execute_action":
                action_to_exec = tool_args.get("action") or tool_args.get("action_id", "")
                policy_eval = self.context.policy_engine.evaluate_policy(
                    action_to_exec, self.context.simulator.get_state()
                )

                if policy_eval.requires_authorization:
                    if auto_authorize:
                        self.context.policy_engine.authorize_action(action_to_exec)
                    else:
                        state.waiting_for_authorization = True
                        state.pending_action = action_to_exec
                        state.add_event(
                            tool=tool_name,
                            status="awaiting_authorization",
                            summary=f"Action '{action_to_exec}' requires Human-in-the-Loop authorization.",
                            details=policy_eval.model_dump(),
                        )
                        return state

            # Execute the tool via authoritative registry
            result = self.registry.execute(tool_name, self.context, tool_args)
            state.tool_calls_count += 1

            # Generate informative event summary
            summary = self._create_summary_for_tool(tool_name, tool_args, result)
            state.add_event(
                tool=tool_name,
                status="completed" if result.get("success", True) is not False else "error",
                summary=summary,
                details=result,
            )

            # Record in message history
            call_id = f"call_{state.current_step}_{tool_name}"
            state.messages.append({
                "role": "assistant",
                "content": response.thought or "",
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args),
                        },
                    }
                ],
            })
            state.messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": call_id,
                "content": json.dumps(result),
            })

            # Track artifacts
            if tool_name == "execute_action":
                state.last_action = tool_args.get("action")
                state.last_execution_result = result
            elif tool_name == "verify_action":
                state.last_verification_result = result
            elif tool_name == "replan":
                state.replan_count += 1

        elif response.type == "message":
            state.messages.append({
                "role": "assistant",
                "content": response.content or "",
            })
            state.final_summary = response.content
            state.completed = True

        return state

    def run(
        self,
        incident_id: str = "INC-GPS-001",
        goal: str = "Investigate flight telemetry anomaly, isolate corrupted sensors, and recover safe flight operations.",
        auto_authorize: bool = False,
    ) -> AgentState:
        """
        Runs the agent loop until completion, waiting for authorization, or hitting MAX_STEPS.
        """
        self.start_investigation(incident_id, goal)

        while not self.state.completed and self.state.current_step < self.MAX_STEPS:
            self.step(auto_authorize=auto_authorize)
            if self.state.waiting_for_authorization:
                break

        return self.state

    def authorize(self, action_id: str, auto_resume: bool = True) -> AgentState:
        """
        Authorizes a pending action and optionally resumes agent execution.
        """
        if not self.state:
            raise ValueError("No active agent investigation to authorize.")

        self.context.policy_engine.authorize_action(action_id)
        self.state.waiting_for_authorization = False
        self.state.pending_action = None

        if auto_resume:
            while not self.state.completed and self.state.current_step < self.MAX_STEPS:
                self.step(auto_authorize=True)
                if self.state.waiting_for_authorization:
                    break

        return self.state

    def _create_summary_for_tool(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]) -> str:
        if tool_name == "get_system_state":
            mode = result.get("navigation_mode", "UNKNOWN")
            status = result.get("mission_status", "UNKNOWN")
            return f"System telemetry retrieved: Mode={mode}, Status={status}."

        if tool_name == "get_observations":
            res = result.get("residual", 0.0)
            score = result.get("anomaly_score", 0.0)
            return f"Observations analyzed: Position residual={res:.1f}m, Anomaly score={score:.2f}."

        if tool_name == "get_trust":
            gps_t = result.get("gps_trust", 1.0)
            imu_t = result.get("imu_trust", 1.0)
            return f"Sensor trust calibrated: GPS={gps_t:.2f}, IMU={imu_t:.2f}."

        if tool_name == "generate_hypotheses":
            hyps = result.get("hypotheses", [])
            top = hyps[0].get("title", "Unknown") if hyps else "None"
            return f"Synthesized {len(hyps)} hypotheses. Primary lead: {top}."

        if tool_name == "get_mission_impact":
            risk = result.get("operational_risk", 0.0)
            urgency = result.get("recommendation_urgency", "NORMAL")
            return f"Mission impact assessed: Operational risk={risk:.2f}, Urgency={urgency}."

        if tool_name == "get_dependency_graph":
            nodes = result.get("nodes", [])
            return f"Dependency graph mapped ({len(nodes)} nodes) connecting sensors to mission goals."

        if tool_name == "generate_actions":
            acts = result.get("actions", [])
            return f"Generated {len(acts)} candidate recovery actions."

        if tool_name == "simulate_action":
            act = result.get("action_id", "")
            risk = result.get("predicted_risk", 0.0)
            outcome = result.get("recommendation", "")
            return f"Simulated '{act}': Predicted Risk={risk:.2f}. Result={outcome}."

        if tool_name == "evaluate_policy":
            act = result.get("action_id", "")
            status = result.get("status", "")
            return f"Policy evaluated for '{act}': {status}."

        if tool_name == "execute_action":
            act = result.get("action_id", "")
            mode = result.get("new_mode", "")
            return f"Authoritative execution of '{act}' succeeded. Navigation mode={mode}."

        if tool_name == "verify_action":
            ver = result.get("verified", False)
            reason = result.get("reason", "")
            return f"Verification {'PASSED' if ver else 'FAILED'}: {reason}"

        if tool_name == "replan":
            rec = result.get("recommended_action", "")
            return f"Replanning triggered: Recommended next action is '{rec}'."

        return f"Executed tool '{tool_name}'."
