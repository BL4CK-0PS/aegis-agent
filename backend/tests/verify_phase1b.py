"""
Live Verification Script for Phase 1B LLM Tool Calling:
Reset -> Fault -> Run
"""

import json
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

print("=== 1. RESET ===")
r_reset = client.post("/api/v1/reset")
print(f"Status Code: {r_reset.status_code}")
print(json.dumps(r_reset.json(), indent=2))

print("\n=== 2. INJECT GPS FAULT ===")
r_fault = client.post("/api/v1/scenario/gps-integrity?bias=6.5")
print(f"Status Code: {r_fault.status_code}")
print(json.dumps(r_fault.json(), indent=2))

print("\n=== 3. AGENT RUN (REAL LLM / BOUNDED TOOL CALLING RUNTIME) ===")
r_run = client.post(
    "/api/v1/agent/run",
    json={
        "incident_id": "INC-PHASE1B-001",
        "goal": "Investigate flight telemetry anomaly and isolate degraded sensors.",
    },
)
print(f"Status Code: {r_run.status_code}")
run_data = r_run.json()

print(f"\nAgent ID: {run_data.get('agent_id')}")
print(f"Incident ID: {run_data.get('incident_id')}")
print(f"Status: {run_data.get('status')}")
print(f"Rounds: {run_data.get('rounds')}")
print(f"Tool Calls Count: {run_data.get('tool_calls_count')}")
print(f"Provider Used: {run_data.get('provider_used')}")

print("\n--- ACTUAL TOOL EXECUTION TRACE ---")
for t in run_data.get("trace", []):
    print(f"  Step {t['step']}: Tool '{t['tool']}' -> Status: {t['status']}")
    print(f"         Summary: {t['summary']}")

print("\n--- FINAL AGENT CONCLUSION ---")
print(run_data.get("final_summary"))
