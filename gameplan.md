# AEGIS — Full 2-Person Game Plan

We now have the **official website timeline + email requirements**, so this is the plan I would actually execute today.

The central rule:

> **Person A owns the agent and decision system. Person B owns the simulated world and user-facing system.**

Neither person should casually modify the other's core architecture after 4 PM. That is how hackathons turn into archaeological sites.

---

# 1. Final architecture

```text
                         ┌───────────────────────┐
                         │       USER / JUDGE     │
                         │    RUN INCIDENT       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      REACT UI         │
                         │     PERSON B          │
                         └───────────┬───────────┘
                                     │
                              REST / WebSocket
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                          │
│                          PERSON A                                │
│                                                                 │
│  ┌─────────────────┐       ┌───────────────────────────────┐    │
│  │  AGENT RUNTIME  │──────▶│       TOOL REGISTRY           │    │
│  │                 │       └──────────────┬────────────────┘    │
│  │ LLM             │                      │                     │
│  │ Reasoning       │          ┌───────────┼───────────┐         │
│  │ Planning        │          │           │           │         │
│  └─────────────────┘          ▼           ▼           ▼         │
│                           Observe      Analyze       Action      │
│                              │           │             │        │
│                              ▼           ▼             ▼        │
│                         ┌─────────────────────────────────┐     │
│                         │        AEGIS CORE                │     │
│                         │                                 │     │
│                         │ Evidence                         │     │
│                         │ Trust                            │     │
│                         │ Risk                             │     │
│                         │ Policy                           │     │
│                         │ Simulation                       │     │
│                         │ Execution                        │     │
│                         │ Verification                     │     │
│                         │ Replanning                       │     │
│                         └──────────────┬──────────────────┘     │
└────────────────────────────────────────┼────────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │ DRONE SIMULATOR     │
                              │ PERSON B             │
                              │                     │
                              │ Telemetry            │
                              │ GPS                  │
                              │ IMU                  │
                              │ Fault Injection      │
                              │ Mission              │
                              └─────────────────────┘
```

---

# 2. The single demo scenario

Do **not** build multiple scenarios first.

We build one extremely polished scenario:

## GPS integrity failure

```text
Mission starts
     ↓
Drone flying normally
     ↓
GPS becomes corrupted
     ↓
Telemetry disagreement detected
     ↓
AEGIS investigates
     ↓
GPS trust decreases
     ↓
Mission risk increases
     ↓
Agent generates response options
     ↓
Agent simulates them
     ↓
Best safe action selected
     ↓
Policy gate
     ↓
Human approval
     ↓
Execute
     ↓
Verification
     ↓
Verification deliberately fails
     ↓
Agent replans
     ↓
Safe mode
     ↓
Verification succeeds
```

That's the entire hackathon story.

---

# 3. Person A — Agent + Backend + Decision Intelligence

## Person A owns

```text
backend/
├── app/
│   ├── core/
│   ├── tools/
│   ├── agent/
│   ├── policy/
│   ├── execution/
│   └── main.py
│
├── tests/
├── Dockerfile
├── requirements.txt
└── agent.yaml
```

Person A should **not** spend the day designing React.

---

# 4. Person A Phase 1 — 9:00–10:00

## Stabilize existing core

Start from the backend we've already defined.

### Verify

```text
models.py
simulator.py
trust.py
evidence.py
risk.py
```

Run:

```bash
pytest -q
```

Expected:

```text
all tests passed
```

Then test:

```http
POST /api/v1/scenario/gps-integrity
```

and:

```http
GET /api/v1/state
```

and:

```http
POST /api/v1/agent/investigate
```

### Deliverable

```text
Deterministic investigation works.
```

---

# 5. Person B Phase 1 — 9:00–10:00

Person B builds the UI skeleton.

## Screen

```text
┌─────────────────────────────────────────────┐
│ AEGIS                         MISSION ACTIVE │
├───────────────────┬─────────────────────────┤
│                   │                         │
│ Drone             │ Mission Graph           │
│ Visualization     │                         │
│                   │ GPS → Navigation        │
│                   │       ↓                 │
│ Telemetry         │   Route Following       │
│                   │                         │
├───────────────────┴─────────────────────────┤
│ Agent Investigation                         │
│                                             │
│ Waiting for incident...                     │
├─────────────────────────────────────────────┤
│ Mission Status: NORMAL                     │
└─────────────────────────────────────────────┘
```

### Person B needs:

- React
- TypeScript
- Tailwind
- simple drone visualization
- telemetry cards
- agent event panel

No beautiful animations yet.

---

# 6. 10:00–11:00

## Person A

Build the complete tool registry.

Minimum:

```text
get_system_state
get_observations
get_trust
generate_hypotheses
get_mission_impact
```

Then add:

```text
get_dependency_graph
generate_actions
simulate_action
evaluate_policy
execute_action
verify_action
replan
```

But implement them in stages.

### First five must work before 11.

---

## Person B

Connect UI to:

```http
GET /api/v1/state
```

and:

```http
POST /api/v1/tick
```

The drone should move.

The UI should update.

### Deliverable

Judge can see:

```text
Drone moving
Telemetry changing
Mission progress increasing
```

---

# 7. 11:00 Mentor Session #1

Both people attend.

### Show:

```text
Drone
 ↓
GPS failure
 ↓
AEGIS detects anomaly
 ↓
Agent investigates
```

### Ask mentors:

1. Does this clearly qualify as an AI agent?
2. Is the workflow sufficiently action-oriented?
3. Is Developer & AI the right domain?
4. Does the demo communicate the value within 30 seconds?
5. Any concerns about the submission format?

Don't ask:

> "Do you like our project?"

That's emotionally comforting and technically useless.

---

# 8. 11:15–12:00

## Person A

Implement actual LLM integration.

Architecture:

```text
Agent Runtime
      │
      ▼
LLM Provider
      │
      ▼
Tool Call
      │
      ▼
Tool Registry
      │
      ▼
Structured Result
      │
      ▼
LLM
```

Use a provider abstraction:

```python
class LLMProvider:
    def chat(...)
```

Then the actual model can be changed without rewriting the agent.

---

## Person B

Build:

### Agent trace panel

```text
AGENT ACTIVITY

✓ System state retrieved
✓ Telemetry analyzed
✓ Trust evaluated
✓ Hypotheses generated
→ Assessing mission impact...
```

The UI should visually show the agent working.

This is important because judges can't award agentic capability they can't see.

---

# 9. 12:00–1:00

## Person A

Get actual tool calling working.

Agent should be able to decide:

```text
get_system_state()
```

then:

```text
get_observations()
```

then:

```text
get_trust()
```

etc.

### Critical test

Remove the deterministic planner.

The LLM should actually select tools.

---

## Person B

Build:

### Evidence panel

```text
EVIDENCE

E01
GPS residual: 8.4m
Source: GPS / IMU comparison

E02
GPS trust: 0.31
Source: trust engine

E03
Mission risk: HIGH
Source: mission impact engine
```

### Hypotheses panel

```text
H1 GPS integrity degradation    0.91
H2 Sensor noise                 0.06
H3 IMU issue                    0.03
```

---

# 10. 1:00 PM Break

Both stop.

No coding.

No architecture discussion.

No "I'll just quickly fix..."

Eat.

---

# 11. 2:00 Mentor Session #2

Now show the actual agent.

The key demo:

```text
Incident
 ↓
Agent
 ↓
Tool calls
 ↓
Evidence
 ↓
Hypothesis
 ↓
Mission impact
```

Ask for feedback specifically on:

> **What single thing would make this feel more like an autonomous agent rather than an AI-powered analytics dashboard?**

The answer should reinforce our action/recovery loop.

---

# 12. 2:15–3:00

# PERSON A — Action Engine

Implement:

```text
generate_actions()
```

Return:

```json
{
  "actions": [
    {
      "id": "continue_gps",
      "name": "Continue GPS",
      "risk": 0.82
    },
    {
      "id": "switch_inertial",
      "name": "Switch to Inertial",
      "risk": 0.42
    },
    {
      "id": "safe_mode",
      "name": "Enter Safe Mode",
      "risk": 0.15
    }
  ]
}
```

---

# 13. Person B — 2:15–3:00

Build:

## Candidate action UI

```text
RESPONSE OPTIONS

┌─────────────────────────────────────┐
│ Continue GPS                        │
│ Risk: HIGH                          │
│ Mission continuity: 42%             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Switch to Inertial                  │
│ Risk: MEDIUM                        │
│ Mission continuity: 71%             │
│                                     │
│ RECOMMENDED                         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Safe Mode                           │
│ Risk: LOW                           │
│ Mission continuity: 0%              │
└─────────────────────────────────────┘
```

---

# 14. 3:00–4:00

## Person A

Implement:

```text
simulate_action()
```

The simulation must be deterministic.

For example:

```text
continue_gps
→ high risk

switch_inertial
→ moderate risk

safe_mode
→ low risk
```

Then:

```text
evaluate_policy()
```

Example:

```python
if action == "continue_gps" and gps_trust < 0.4:
    deny()
```

---

## Person B

Build:

### Simulation visualization

Show:

```text
CURRENT STATE
        │
        ├──── Continue GPS ── HIGH RISK
        │
        ├──── Inertial ────── MEDIUM RISK
        │
        └──── Safe Mode ───── LOW RISK
```

Make the selected action visually obvious.

---

# 15. 4:00 PM — MIDPOINT CHECK

## HARD CHECKPOINT

At this point:

### Person A must have

```text
✓ Agent
✓ Tools
✓ Evidence
✓ Trust
✓ Risk
✓ Candidate actions
✓ Simulation
✓ Policy
```

### Person B must have

```text
✓ Dashboard
✓ Live telemetry
✓ Agent trace
✓ Evidence
✓ Hypotheses
✓ Action cards
✓ Simulation results
```

If these aren't working:

## STOP adding features.

From 4 PM onward, we're finishing the core.

---

# 16. 4:00–5:00

# Governance + Human Authorization

## Person A

Implement:

```text
evaluate_policy()
```

and:

```text
authorize_action()
```

Flow:

```text
Agent recommendation
       ↓
Policy
       ↓
Risk classification
       ↓
Human authorization required
       ↓
Approved / rejected
```

---

## Person B

Build authorization UI:

```text
┌──────────────────────────────────────┐
│ ACTION REQUIRES AUTHORIZATION        │
│                                      │
│ Switch to Inertial Navigation        │
│                                      │
│ Mission Risk: MEDIUM                 │
│ GPS Trust: 0.31                      │
│ Expected Safety: 78%                 │
│                                      │
│ [ APPROVE ]       [ REJECT ]         │
└──────────────────────────────────────┘
```

---

# 17. 5:00–5:45

# Execution

## Person A

Implement:

```text
execute_action()
```

Supported:

```text
SWITCH_TO_INERTIAL
SAFE_MODE
```

The execution layer changes simulator state.

The LLM never directly mutates simulator state.

---

## Person B

Show execution:

```text
ACTION APPROVED
       ↓
EXECUTING
       ↓
Navigation Mode:
INERTIAL
       ↓
MISSION STATE:
DEGRADED
```

---

# 18. 5:45–6:00

# Verification

## Person A

Implement:

```text
verify_action()
```

Checks:

```text
navigation_mode
GPS trust
position residual
mission risk
mission status
```

Return:

```json
{
  "verified": true,
  "status": "safe",
  "reason": "Mission risk reduced below policy threshold."
}
```

---

# 19. 6:00 PM — FINAL SPRINT

This is where the website explicitly says:

> **Final Sprint**

Treat it literally.

The architecture is frozen.

---

# 20. 6:00–6:45

# The killer feature: Recovery

## Person A

Implement deliberate verification failure.

Example:

```text
switch_inertial
       ↓
execute
       ↓
verify
       ↓
FAIL
```

Then:

```text
replan()
```

Agent receives:

```text
Previous action failed verification.

Reason:
Position residual remains above threshold.

Available alternatives:
SAFE_MODE
```

Then selects:

```text
SAFE_MODE
```

---

## Person B

Display:

```text
⚠ VERIFICATION FAILED

Reason:
Navigation residual remains unsafe.

AGENT REPLANNING...

↓

NEW PLAN

1. Enter Safe Mode
2. Stabilize navigation
3. Verify mission state
```

Then:

```text
✓ RECOVERY SUCCESSFUL
```

This is the climax of the demo.

---

# 21. 6:45–7:15

# Full integration test

Both people stop adding functionality.

Run the entire flow:

```text
RESET
 ↓
NORMAL
 ↓
GPS FAULT
 ↓
AGENT
 ↓
INVESTIGATION
 ↓
ACTION
 ↓
SIMULATION
 ↓
POLICY
 ↓
AUTHORIZATION
 ↓
EXECUTION
 ↓
VERIFICATION FAILURE
 ↓
REPLAN
 ↓
SAFE MODE
 ↓
VERIFICATION SUCCESS
```

Do it **at least three times**.

---

# 22. 7:15–7:45

# Docker + API + Manifest

## Person A

Prepare:

```text
Dockerfile
requirements.txt
agent.yaml
.env.example
README.md
```

And endpoints:

```http
GET  /health

POST /api/v1/agent/run

POST /api/v1/scenario/gps-integrity

POST /api/v1/reset
```

The exact `agent.yaml` schema should follow the official aiKart manifest guide, not something we invent because YAML is apparently humanity's chosen method for making configuration files look deceptively simple.

---

## Person B

Prepare production frontend:

```text
npm run build
```

Verify:

```text
API URL
CORS
WebSocket/SSE
static assets
```

No dev-only dependency should break the final demo.

---

# 23. 7:45–8:00

# Submission freeze

Create final Git commit:

```bash
git add .
git commit -m "Bharat Agentic 2026 final"
git push
```

Tag:

```bash
git tag v1.0.0
git push --tags
```

Then stop touching the code unless something is actually broken.

---

# 24. 8:00 PM — Submission Opens

One person submits.

One person verifies.

## Person A

Handles:

- agent endpoint
- Docker
- manifest
- GitHub
- technical details

## Person B

Handles:

- demo video
- screenshots
- pitch deck
- submission copy

Both verify the final Google Form before submitting.

---

# 25. 8:00–8:30

# Demo Video

Use exactly one scenario.

### Timeline

| Time | Demo |
|---|---|
| 0:00–0:15 | Normal mission |
| 0:15–0:30 | GPS failure |
| 0:30–0:55 | Agent investigates |
| 0:55–1:15 | Evidence + hypotheses |
| 1:15–1:35 | Simulated actions |
| 1:35–1:50 | Policy + authorization |
| 1:50–2:05 | Execution |
| 2:05–2:20 | Verification failure |
| 2:20–2:40 | Replanning |
| 2:40–2:55 | Recovery |
| 2:55–3:00 | Final result |

---

# 26. 5-slide pitch deck

Don't make 18 slides. The judges have other humans to deal with.

## Slide 1 — Problem

### **Autonomous systems can fail under uncertainty**

GPS degradation can create:

- incorrect state estimation
- unsafe navigation
- mission degradation
- cascading operational impact

---

## Slide 2 — AEGIS

### **Evidence-driven agentic decision intelligence**

Show:

```text
Observe
 ↓
Reason
 ↓
Investigate
 ↓
Simulate
 ↓
Govern
 ↓
Act
 ↓
Verify
 ↓
Recover
```

---

## Slide 3 — Agent Architecture

Show:

```text
LLM Agent
   ↓
Tools
   ↓
AEGIS Core
   ↓
Simulator
   ↓
Action
   ↓
Verification
   ↓
Replanning
```

---

## Slide 4 — Demo / Impact

Show the actual incident.

```text
GPS fault
 ↓
Risk detected
 ↓
Response simulated
 ↓
Action executed
 ↓
Verification failed
 ↓
Recovery
```

---

## Slide 5 — Why AEGIS

```text
Agentic
Evidence-driven
Governed
Verifiable
Recoverable
Scalable
```

Then:

> **From uncertain observations to governed, verifiable action.**

---

# 27. Division of responsibility

## PERSON A

### Backend / Agent / AI

```text
CORE
├── models
├── simulator interface
├── evidence
├── trust
├── risk
│
TOOLS
├── observation tools
├── analysis tools
├── action tools
├── policy tools
├── verification tools
│
AGENT
├── LLM
├── tool calling
├── planner
├── state
├── reasoning loop
├── replanning
│
DEPLOYMENT
├── FastAPI
├── Docker
├── Agent API
└── Manifest
```

---

# 28. Person B

### Simulator + Frontend + Demo

```text
SIMULATOR
├── drone state
├── telemetry
├── GPS
├── IMU
├── fault injection
├── mission
├── action effects
└── verification effects

FRONTEND
├── dashboard
├── drone visualization
├── telemetry
├── mission graph
├── agent trace
├── evidence
├── hypotheses
├── trust
├── actions
├── policy
├── authorization
└── recovery

SUBMISSION
├── demo video
├── screenshots
└── pitch deck
```

---

# 29. Shared integration contract

This is extremely important.

Person A and B should agree on these API objects **before coding heavily**.

## State

```json
{
  "time": 12.0,
  "position": {
    "x": 120.5,
    "y": 84.2
  },
  "velocity": {
    "x": 10.2,
    "y": 5.1
  },
  "navigation_mode": "GPS_ASSISTED",
  "gps_trust": 0.31,
  "imu_trust": 0.92,
  "mission_progress": 0.42,
  "mission_status": "DEGRADED"
}
```

## Agent event

```json
{
  "step": 4,
  "tool": "get_trust",
  "status": "completed",
  "summary": "GPS trust decreased due to persistent residual."
}
```

## Action

```json
{
  "id": "switch_inertial",
  "name": "Switch to Inertial Navigation",
  "risk": 0.42,
  "mission_continuity": 0.71
}
```

## Verification

```json
{
  "verified": false,
  "reason": "Navigation residual remains above threshold.",
  "next_action_required": true
}
```

Both sides build against these contracts.

---

# 30. Shared Git strategy

Use:

```text
main
develop
```

Person A:

```text
feature/agent
feature/tools
feature/policy
feature/execution
```

Person B:

```text
feature/frontend
feature/simulator
feature/demo
```

Merge frequently before 4 PM.

After 6 PM:

> **No unnecessary branching.**

---

# 31. Emergency cut plan

If you're behind schedule:

### At 12 PM

Cut:

- advanced UI
- database

Keep:

- agent
- tools

### At 2 PM

Cut:

- sophisticated dependency graph

Keep:

- action simulation

### At 4 PM

Cut:

- extra scenarios
- advanced optimizer
- persistence
- fancy visualization

Keep:

```text
Agent
Tools
Action
Policy
Execution
Verification
Replanning
```

### At 6 PM

Cut **everything except integration and submission**.

---

# 32. Final definition of "DONE"

AEGIS is done when this exact sentence can truthfully describe the system:

> **AEGIS receives a simulated autonomous-system incident, uses an AI agent to investigate it through typed tools, reasons over evidence and system trust, evaluates mission impact, simulates candidate responses, passes the selected response through a policy gate, executes the authorized action, verifies the result, and replans when verification fails.**

If we can demonstrate that reliably, we have fulfilled the core challenge.

Everything else is decoration.

---

# 33. Today's command structure

## Person A

**Think in terms of:**

> **Agent → Tools → Decision → Action → Verification**

## Person B

**Think in terms of:**

> **World → Visualization → Agent Trace → Human Interaction → Demo**

## Both

**Think in terms of:**

> **One incident. One agent. One closed loop. One excellent demo.**

That is the entire 12-hour strategy. The biggest danger now isn't technical difficulty. It's scope creep. AEGIS already has enough substance to score on agentic capability, technical implementation, innovation, and demo quality. The job today is to make that substance **visible, executable, and deployable** before 9 PM.