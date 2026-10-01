# AEGIS — Person A Master Build Prompt

## Role
You are Person A for AEGIS in Bharat Agentic 2026. Own the backend, agent runtime, decision-intelligence core, tools, policy, execution, verification, replanning, API, Docker, tests, and agent submission packaging.

## Project
**AEGIS — Autonomous Evidence-driven Governance and Intelligent Safety**

Tagline: **Mission-aware agentic decision intelligence for autonomous systems.**

Core scenario: a simulated autonomous drone suffers a GPS integrity incident. The agent must investigate uncertainty, gather evidence, assess mission impact, evaluate responses, execute an authorized action, verify it, and recover/replan if verification fails.

## Core loop
Understand → Reason → Plan → Use Tools → Act → Verify → Replan → Deliver

Implementation:
Observe → Investigate → Evidence → Hypotheses → Trust → Mission Impact → Actions → Simulation → Policy → Authorization → Execute → Verify → Recover/Replan

## Critical engineering rule
The LLM is NOT the safety authority.

Use:
LLM → typed tool call → tool registry → application validation → deterministic core → structured result → LLM

Never let raw model output directly mutate simulator state.

## Current backend structure
```text
backend/
├── app/
│   ├── core/
│   │   ├── models.py
│   │   ├── simulator.py
│   │   ├── trust.py
│   │   ├── evidence.py
│   │   └── risk.py
│   ├── tools/
│   │   ├── context.py
│   │   ├── registry.py
│   │   ├── state_tools.py
│   │   └── analysis_tools.py
│   └── agent/
│       ├── state.py
│       ├── planner.py
│       └── runtime.py
├── tests/
├── requirements.txt
└── Dockerfile
```

## Final tool set
```text
get_system_state
get_observations
get_trust
generate_hypotheses
get_mission_impact
get_dependency_graph
generate_actions
simulate_action
evaluate_policy
execute_action
verify_action
replan
```

Build the first five before expanding.

## Real agent requirement
Replace the deterministic planner with actual LLM tool calling. The model must select tools, receive structured results, reason over them, select further tools, choose an action, pass policy, execute only when authorized, verify, and replan after failure.

Do not fake tool calling with a hard-coded sequence.

Enforce a maximum agent step count such as `MAX_STEPS = 15`.

## Actions
Start with exactly:
1. Continue GPS-assisted navigation
2. Switch to inertial navigation
3. Enter safe mode

Each action must be simulated before execution.

## Counterfactual flow
Generate actions → simulate each → compare outcomes → select valid action → policy → authorization → execution.

## Policy
Application-authoritative. Example:
- GPS trust below threshold + GPS-dependent action → deny.
- High mission risk → human authorization required.
- Only approved actions may execute.

The model cannot override policy.

## Execution
Implement:
`execute_action()`

Supported initial actions:
- `SWITCH_TO_INERTIAL`
- `SAFE_MODE`

Only validated application code can mutate simulator state.

## Verification
Implement `verify_action()` using:
- navigation mode
- GPS trust
- position residual
- mission risk
- mission status

Return structured verification results.

## Recovery
The demo must support:
Execute → Verify → FAIL → Replan → New Action → Policy → Execute → Verify → SUCCESS.

Make verification failure deliberate and deterministic for the demo.

## API
At minimum:
```text
GET  /health
GET  /api/v1/state
POST /api/v1/reset
POST /api/v1/scenario/gps-integrity
POST /api/v1/tick
GET  /api/v1/tools
POST /api/v1/agent/investigate
POST /api/v1/agent/run
```

Keep API contracts stable for Person B.

## Integration objects
State:
```json
{
  "time": 12.0,
  "position": {"x": 120.5, "y": 84.2},
  "velocity": {"x": 10.2, "y": 5.1},
  "navigation_mode": "GPS_ASSISTED",
  "gps_trust": 0.31,
  "imu_trust": 0.92,
  "mission_progress": 0.42,
  "mission_status": "DEGRADED"
}
```

Agent event:
```json
{
  "step": 4,
  "tool": "get_trust",
  "status": "completed",
  "summary": "GPS trust decreased due to persistent residual."
}
```

Action:
```json
{
  "id": "switch_inertial",
  "name": "Switch to Inertial Navigation",
  "risk": 0.42,
  "mission_continuity": 0.71
}
```

Verification:
```json
{
  "verified": false,
  "reason": "Navigation residual remains above threshold.",
  "next_action_required": true
}
```

## LLM provider
Use a provider abstraction such as:
```python
class LLMProvider:
    def chat(self, messages, tools):
        ...
```
Keep the runtime independent of the model provider.

## Testing
Test:
- GPS fault
- anomaly
- trust
- mission impact
- tool registry
- schemas
- agent investigation
- real tool calling
- policy denial
- execution
- verification
- replanning
- prevention of direct LLM state mutation

## Timeline
9:00–10:00 core
10:00–11:00 tools
11:00 mentor
11:15–1:00 real LLM tool calling
1:00 break
2:00 mentor
2:15–4:00 actions/simulation/policy
4:00 midpoint
4:00–5:45 authorization/execution/verification
5:45–6:00 verification
6:00 final sprint
6:00–7:00 recovery/replanning
7:00–7:45 integration/Docker/API/manifest
7:45–8:00 freeze
8:00–9:00 submission support/final fixes

## Scope cuts
Do not add multi-agent, RAG, custom ML, real drone control, PX4, ROS2, swarm intelligence, blockchain, mobile app, or multiple domains unless the core is already completely stable.

## Definition of done
From a clean reset:
GPS fault → agent investigation → evidence → hypothesis → trust → mission impact → candidate actions → simulation → policy → authorization → execution → verification failure → replan → safe mode → verification success.

Then package in Docker and expose the agent API.
