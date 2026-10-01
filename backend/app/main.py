"""
AEGIS FastAPI Application Entrypoint
Exposes HTTP REST API for operator control, simulator progression,
agent investigation, and integration with Person B's frontend.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent.llm_runtime import LLMRunResult, LLMRuntime
from app.agent.runtime import AgentRuntime
from app.agent.state import AgentState
from app.core.execution import ExecutionAdapter
from app.core.models import SystemState
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext

app = FastAPI(
    title="AEGIS — Bharat Agentic 2026 Core",
    description="Autonomous Evidence-driven Governance and Intelligent Safety Agent Core API",
    version="1.0.0",
)

# Enable CORS for React frontend (Person B)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global runtime state
simulator = DroneSimulator(seed=42, deliberate_failure_enabled=True)
policy_engine = PolicyEngine()
execution_adapter = ExecutionAdapter(simulator, policy_engine)
verification_engine = VerificationEngine(simulator, deliberate_failure_enabled=True)
tool_context = ToolContext(
    simulator=simulator,
    policy_engine=policy_engine,
    execution_adapter=execution_adapter,
    verification_engine=verification_engine,
)
tool_registry = create_default_tool_registry()
agent_runtime = AgentRuntime(tool_registry, tool_context)
llm_runtime = LLMRuntime(tool_registry, tool_context)


class AuthorizeRequest(BaseModel):
    action_id: str = Field(..., description="Action ID to authorize: switch_inertial or safe_mode.")
    auto_resume: bool = Field(True, description="Whether to continue agent execution after authorizing.")


class AgentRunRequest(BaseModel):
    incident_id: str = "INC-GPS-001"
    goal: str = "Investigate flight telemetry anomaly, isolate corrupted sensors, and recover safe flight operations."
    auto_authorize: bool = False


# --- Health & Diagnostic Endpoints ---

@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "aegis",
        "version": "1.0.0",
        "mode": "simulator_governed",
    }


# --- Simulator State & Controls ---

@app.get("/api/v1/state", response_model=SystemState, tags=["Simulator"])
def get_state() -> SystemState:
    """Returns canonical system state matching Person B's integration contract."""
    return simulator.get_state()


@app.post("/api/v1/reset", tags=["Simulator"])
def reset_system(seed: Optional[int] = 42) -> Dict[str, Any]:
    """Resets simulator, governance authorizer, and agent runtime to initial nominal state."""
    simulator.reset(seed=seed)
    policy_engine.reset_authorizations()
    verification_engine.reset()
    agent_runtime.start_investigation()
    return {
        "status": "reset_success",
        "state": simulator.get_state(),
    }


@app.post("/api/v1/scenario/gps-integrity", tags=["Simulator"])
def inject_gps_integrity_fault(bias: float = 6.0) -> Dict[str, Any]:
    """Injects GPS integrity fault, initiating divergence between GPS and inertial trajectory."""
    simulator.inject_gps_fault(initial_bias=bias)
    return {
        "status": "fault_injected",
        "scenario": "gps-integrity",
        "initial_bias": bias,
        "state": simulator.get_state(),
    }


@app.post("/api/v1/tick", response_model=SystemState, tags=["Simulator"])
def tick_simulation() -> SystemState:
    """Advances simulation forward by one time step."""
    return simulator.tick()


# --- Tool Registry ---

@app.get("/api/v1/tools", tags=["Tools"])
def list_tools() -> Dict[str, Any]:
    """Returns list of registered typed tools and their schemas."""
    tools = tool_registry.list_tools()
    return {
        "total_tools": len(tools),
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
            }
            for t in tools
        ],
    }


# --- Agent Endpoints ---

@app.post("/api/v1/agent/investigate", response_model=AgentState, tags=["Agent"])
def agent_investigate(req: Optional[AgentRunRequest] = None) -> AgentState:
    """
    Initializes and executes Phase 1A deterministic 5-step diagnostic investigation:
    get_system_state -> get_observations -> get_trust -> generate_hypotheses -> get_mission_impact.
    """
    incident_id = req.incident_id if req else "INC-GPS-001"
    goal = req.goal if req else "Investigate the navigation integrity incident."
    return agent_runtime.investigate(incident_id=incident_id, goal=goal)


@app.post("/api/v1/agent/step", response_model=AgentState, tags=["Agent"])
def agent_step(auto_authorize: bool = False) -> AgentState:
    """Advances agent investigation by a single step (useful for stepped UI animation)."""
    return agent_runtime.step(auto_authorize=auto_authorize)


@app.post("/api/v1/agent/run", response_model=LLMRunResult, tags=["Agent"])
def agent_run(req: Optional[AgentRunRequest] = None) -> LLMRunResult:
    """Runs bounded LLM multi-turn tool-calling investigation loop."""
    incident_id = req.incident_id if req else "INC-GPS-001"
    goal = req.goal if req else "Investigate flight telemetry anomaly and determine sensor integrity."
    return llm_runtime.run(incident_id=incident_id, goal=goal)


@app.post("/api/v1/agent/authorize", response_model=AgentState, tags=["Agent"])
def authorize_action(req: AuthorizeRequest) -> AgentState:
    """Human-in-the-Loop operator authorization endpoint. Approves action and resumes loop."""
    try:
        return agent_runtime.authorize(action_id=req.action_id, auto_resume=req.auto_resume)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
