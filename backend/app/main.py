"""
AEGIS FastAPI Application Entrypoint
Exposes HTTP REST API for operator control, simulator progression,
agent investigation, and integration with Person B's frontend.
"""

from __future__ import annotations
import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("aegis.main")

from app.agent.llm_runtime import LLMRunResult, LLMRuntime
from app.agent.runtime import AgentRuntime
from app.agent.state import AgentState
from app.core.execution import ExecutionAdapter
from app.core.models import SystemState
from app.core.policy import PolicyEngine
from app.core.simulator import DroneSimulator
from app.core.verification import VerificationEngine
from app.demo.orchestrator import DemoOrchestrator, DemoResult
from app.tools import create_default_tool_registry
from app.tools.context import ToolContext

from contextlib import asynccontextmanager

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

# Canonical Demo Orchestrator
demo_orchestrator = DemoOrchestrator(
    simulator=simulator,
    policy_engine=policy_engine,
    execution_adapter=execution_adapter,
    verification_engine=verification_engine,
    simulation_engine=tool_context.simulation_engine,
    tool_registry=tool_registry,
    tool_context=tool_context,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-flight verification of simulator, tool registry, policy, and verifier."""
    initial_state = simulator.get_state()
    assert initial_state is not None, "Simulator failed initial state retrieval"
    tools = tool_registry.list_tools()
    assert len(tools) >= 10, f"Expected >= 10 tools, found {len(tools)}"
    assert hasattr(policy_engine, "evaluate_policy"), "Policy engine missing evaluate_policy method"
    assert hasattr(verification_engine, "verify_action"), "Verification engine missing verify_action method"
    logger.info("AEGIS pre-flight startup validation passed: %d tools registered, safety engines active.", len(tools))
    yield


app = FastAPI(
    title="AEGIS — Bharat Agentic 2026 Core",
    description="Autonomous Evidence-driven Governance and Intelligent Safety Agent Core API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React frontend (Development and Containerized Production)
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,*"
)
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthorizeRequest(BaseModel):
    action_id: str = Field(..., description="Action ID to authorize: switch_inertial or safe_mode.")
    auto_resume: bool = Field(True, description="Whether to continue agent execution after authorizing.")


class SimulateRequest(BaseModel):
    action_id: str = Field(..., description="Action ID to simulate: continue_gps, switch_inertial, safe_mode.")


class AgentRunRequest(BaseModel):
    incident_id: str = "INC-GPS-001"
    goal: str = "Investigate flight telemetry anomaly, isolate corrupted sensors, and recover safe flight operations."
    auto_authorize: bool = False


# --- Health & Diagnostic Endpoints ---

@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    provider_name = os.getenv("AEGIS_LLM_PROVIDER", "mock").lower().strip()

    if provider_name in ("openai", "ollama", "live"):
        if hasattr(llm_runtime, "provider") and hasattr(llm_runtime.provider, "client") and llm_runtime.provider.client is not None:
            llm_status = "connected"
        else:
            llm_status = "unavailable"
    else:
        llm_status = "deterministic_fallback"

    demo_mode = os.getenv("AEGIS_DEMO_MODE", "true").lower() in ("true", "1", "yes")

    return {
        "status": "healthy",
        "service": "aegis",
        "version": "1.0.0",
        "demo_mode": demo_mode,
        "llm": llm_status,
        "llm_provider": provider_name,
        "tools_registered": len(tool_registry.list_tools()),
        "simulator": "ready",
        "policy_engine": "active",
        "verification_engine": "active",
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
    if tool_context.simulation_engine:
        tool_context.simulation_engine.reset()
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


# --- Action Simulation & Subsystem Analysis Endpoints ---

class AuthorizeDecisionRequest(BaseModel):
    decision: str = Field("approve", description="Decision: 'approve' or 'deny'.")


@app.post("/api/v1/simulate", tags=["Actions"])
@app.post("/api/v1/action/simulate", tags=["Actions"])
def simulate_action_endpoint(req: SimulateRequest) -> Dict[str, Any]:
    """Runs counterfactual simulation of a candidate response action."""
    return tool_registry.execute("simulate_action", tool_context, {"action": req.action_id})


@app.get("/api/v1/dependency-graph", tags=["Analysis"])
def get_dependency_graph() -> Dict[str, Any]:
    """Returns current system dependency propagation graph."""
    return tool_registry.execute("get_dependency_graph", tool_context, {})


@app.get("/api/v1/mission-impact", tags=["Analysis"])
def get_mission_impact() -> Dict[str, Any]:
    """Returns current operational mission impact and risk assessment."""
    return tool_registry.execute("get_mission_impact", tool_context, {})


@app.get("/api/v1/evidence", tags=["Analysis"])
def get_evidence() -> Dict[str, Any]:
    """Returns synthesized evidence and competing hypotheses."""
    return tool_registry.execute("generate_hypotheses", tool_context, {})


@app.get("/api/v1/actions", tags=["Actions"])
def get_candidate_actions() -> Dict[str, Any]:
    """Returns candidate operational response actions."""
    return tool_registry.execute("generate_actions", tool_context, {})


@app.get("/api/v1/actions/compare", tags=["Actions"])
def compare_candidate_actions() -> Dict[str, Any]:
    """Returns comparative metrics across all candidate response actions."""
    sim_engine = tool_context.simulation_engine
    if not sim_engine:
        from app.core.simulation import SimulationEngine
        sim_engine = SimulationEngine(simulator)
        tool_context.simulation_engine = sim_engine
    return {"comparisons": sim_engine.compare_actions()}


@app.post("/api/v1/actions/{action_id}/simulate", tags=["Actions"])
def simulate_action_by_id(action_id: str) -> Dict[str, Any]:
    """Runs isolated counterfactual simulation for a specific candidate action."""
    return tool_registry.execute("simulate_action", tool_context, {"action": action_id})


@app.post("/api/v1/actions/{action_id}/authorize", tags=["Actions"])
@app.post("/api/v1/authorization/{action_id}", tags=["Actions"])
def authorize_action_by_id(
    action_id: str,
    req: Optional[AuthorizeDecisionRequest] = None,
) -> Dict[str, Any]:
    """
    Explicit authorization endpoint. Validates action existence and policy constraints
    before approving or denying execution permission.
    """
    from app.core.actions import is_valid_action
    if not is_valid_action(action_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action '{action_id}' does not exist in registry.",
        )

    decision = req.decision.lower().strip() if req else "approve"
    if decision == "approve":
        policy_eval = policy_engine.evaluate_policy(action_id, simulator.get_state())
        if policy_eval.status == "DENY" or not policy_eval.allowed and not policy_eval.requires_authorization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action '{action_id}' is denied by governance policy: {policy_eval.reason}",
            )
        policy_engine.authorize_action(action_id)
        return {
            "action_id": action_id,
            "decision": "approve",
            "authorization_status": "APPROVED",
            "message": f"Action '{action_id}' authorized by operator.",
        }
    else:
        policy_engine.deny_action(action_id)
        return {
            "action_id": action_id,
            "decision": "deny",
            "authorization_status": "DENIED",
            "message": f"Action '{action_id}' explicitly denied by operator.",
        }


@app.post("/api/v1/actions/{action_id}/execute", tags=["Actions"])
def execute_action_by_id(action_id: str) -> Dict[str, Any]:
    """Executes a candidate action through the authoritative 6-gate execution adapter."""
    return tool_registry.execute("execute_action", tool_context, {"action": action_id})


@app.post("/api/v1/actions/{action_id}/verify", tags=["Actions"])
def verify_action_by_id(action_id: str) -> Dict[str, Any]:
    """Verifies actual post-action platform state against expected safety invariants."""
    return tool_registry.execute("verify_action", tool_context, {"action": action_id})


# --- Phase 4 Canonical Demo Orchestration Endpoints ---

@app.websocket("/ws/demo")
async def demo_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket event stream for the live dashboard.
    Broadcasts state transitions, telemetry updates, trace steps, and governance gates in real time.
    """
    await websocket.accept()
    demo_orchestrator.register_connection(websocket)
    try:
        import time
        initial_event = {
            "event": "connected",
            "phase": demo_orchestrator.current_phase.value,
            "timestamp": time.time(),
            "demo_id": demo_orchestrator.current_demo_id or "DEMO-IDLE",
            "payload": demo_orchestrator.get_state(),
        }
        await websocket.send_text(json.dumps(initial_event))
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        demo_orchestrator.unregister_connection(websocket)
    except Exception:
        demo_orchestrator.unregister_connection(websocket)


@app.post("/api/v1/demo/run", response_model=DemoResult, tags=["Demo"])
def run_canonical_demo_endpoint(auto_authorize: bool = True) -> DemoResult:
    """
    ONE BUTTON -> COMPLETE AEGIS DECISION LOOP.
    Executes the canonical incident recovery workflow:
    Normal -> Incident -> Investigation -> Action Generation -> Counterfactual Simulation ->
    Policy Gate -> Operator Authorization -> Authoritative Execution -> Intentional Verification Failure ->
    Dynamic Replanning -> Replacement Execution -> Verification Success -> Platform Recovery.
    """
    return demo_orchestrator.run(auto_authorize=auto_authorize)


@app.post("/api/v1/demo/reset", tags=["Demo"])
def reset_canonical_demo_endpoint() -> Dict[str, Any]:
    """Resets simulator, policy, trace, events, and demo state to nominal baseline."""
    return demo_orchestrator.reset()


@app.get("/api/v1/demo/state", tags=["Demo"])
def get_canonical_demo_state() -> Dict[str, Any]:
    """Returns instantaneous demo lifecycle state and telemetry."""
    return demo_orchestrator.get_state()


@app.get("/api/v1/demo/trace", tags=["Demo"])
def get_canonical_demo_trace() -> List[Dict[str, Any]]:
    """Returns complete structured audit trace of all decision loop steps."""
    return demo_orchestrator.get_trace()


@app.get("/api/v1/demo/events", tags=["Demo"])
def get_canonical_demo_events() -> List[Dict[str, Any]]:
    """Returns history of all broadcast demo events."""
    return demo_orchestrator.get_events()



