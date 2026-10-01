"""
Verification Script for Phase 1A AEGIS Core
"""

import json
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

print("=== STEP 5: HEALTH ===")
r = client.get("/api/v1/health")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

print("\n=== STEP 6: NORMAL STATE ===")
client.post("/api/v1/reset")
r = client.get("/api/v1/state")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

print("\n=== STEP 7: INJECT GPS FAULT ===")
r_fault = client.post("/api/v1/scenario/gps-integrity?bias=6.0")
print("Fault Injected:", r_fault.json()["status"])
r_state = client.get("/api/v1/state")
print("Degraded State:")
print(json.dumps(r_state.json(), indent=2))

print("\n=== STEP 8: ADVANCE SIMULATOR (TICKS) ===")
r1 = client.post("/api/v1/tick")
d1 = r1.json()
print(f"Tick 1 -> Time: {d1['time']}, Residual: {d1['residual']}m, GPS Trust: {d1['gps_trust']}, Anomaly Score: {d1['anomaly_score']}")
r2 = client.post("/api/v1/tick")
d2 = r2.json()
print(f"Tick 2 -> Time: {d2['time']}, Residual: {d2['residual']}m, GPS Trust: {d2['gps_trust']}, Anomaly Score: {d2['anomaly_score']}")

print("\n=== STEP 9: TEST TOOLS & AGENT INVESTIGATION ===")
r_tools = client.get("/api/v1/tools")
tools = [t["name"] for t in r_tools.json()["tools"]]
print(f"Total Registered Tools: {len(tools)}")
print("Tools:", tools)

r_inv = client.post("/api/v1/agent/investigate", json={"goal": "Investigate the navigation integrity incident."})
inv_data = r_inv.json()
print(f"\nInvestigation completed: {inv_data['completed']}")
print(f"Events recorded: {len(inv_data['events'])}")
for ev in inv_data["events"]:
    print(f"  Step {ev['step']}: {ev['tool']} -> {ev['summary']}")

print("\n=== STEP 10: HYPOTHESES VERIFICATION ===")
hyp_event = next(e for e in inv_data["events"] if e["tool"] == "generate_hypotheses")
hypotheses = hyp_event["details"]["hypotheses"]
for h in hypotheses:
    h_name = h.get("name") or h.get("title")
    h_conf = h.get("confidence") or h.get("likelihood")
    print(f"  {h['id']}: {h_name} | Confidence: {h_conf}")

print("\n=== CONCLUSION SUMMARY ===")
print(inv_data.get("final_summary"))
