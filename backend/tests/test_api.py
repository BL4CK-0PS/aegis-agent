"""
Tests for FastAPI Endpoints using TestClient
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoints():
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"

    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    assert res2.json()["service"] == "aegis"


def test_state_and_tick_endpoints():
    client.post("/api/v1/reset")
    res = client.get("/api/v1/state")
    assert res.status_code == 200
    data = res.json()
    assert "time" in data
    assert "position" in data
    assert "velocity" in data
    assert "navigation_mode" in data
    assert "gps_trust" in data
    assert "imu_trust" in data
    assert "mission_progress" in data
    assert "mission_status" in data

    # Tick simulation
    tick_res = client.post("/api/v1/tick")
    assert tick_res.status_code == 200
    assert tick_res.json()["time"] > data["time"]


def test_fault_injection_scenario():
    client.post("/api/v1/reset")
    res = client.post("/api/v1/scenario/gps-integrity?bias=7.5")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "fault_injected"
    assert data["state"]["gps_fault_active"] is True
    assert data["state"]["residual"] > 5.0


def test_tools_list_endpoint():
    res = client.get("/api/v1/tools")
    assert res.status_code == 200
    data = res.json()
    assert data["total_tools"] == 12
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_system_state" in tool_names
    assert "simulate_action" in tool_names
    assert "evaluate_policy" in tool_names
    assert "verify_action" in tool_names


def test_agent_investigate_endpoint():
    client.post("/api/v1/reset")
    client.post("/api/v1/scenario/gps-integrity?bias=6.5")

    res = client.post("/api/v1/agent/investigate", json={
        "incident_id": "INC-INV-001",
        "goal": "Investigate the navigation integrity incident.",
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["events"]) == 5
    assert [e["tool"] for e in data["events"]] == [
        "get_system_state",
        "get_observations",
        "get_trust",
        "generate_hypotheses",
        "get_mission_impact",
    ]
    assert data["completed"] is True
    assert "Investigation Complete" in data["final_summary"]


def test_agent_run_endpoint():
    client.post("/api/v1/reset")
    client.post("/api/v1/scenario/gps-integrity?bias=7.0")

    run_res = client.post("/api/v1/agent/run", json={
        "incident_id": "INC-RUN-001",
        "goal": "Test LLM agent run via API",
    })
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["tool_calls_count"] >= 1
    assert len(run_data["trace"]) >= 1
    assert "final_summary" in run_data


def test_agent_authorize_endpoint():
    client.post("/api/v1/reset")
    # Authorize action via API
    auth_res = client.post("/api/v1/agent/authorize", json={
        "action_id": "switch_inertial",
        "auto_resume": False,
    })
    assert auth_res.status_code == 200
