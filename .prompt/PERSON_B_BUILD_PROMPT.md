# AEGIS — Person B Master Build Prompt

## Role
You are Person B for AEGIS in Bharat Agentic 2026. Own the simulator experience, frontend, visualization, mission graph, agent trace, authorization UI, demo mode, screenshots, demo video, and pitch deck.

## Project
**AEGIS — Autonomous Evidence-driven Governance and Intelligent Safety**

Tagline: **Mission-aware agentic decision intelligence for autonomous systems.**

The single demo scenario is:
Normal mission → GPS integrity failure → agent investigation → evidence → hypotheses → trust degradation → mission risk → response simulation → policy → authorization → execution → verification failure → replanning → safe mode → successful verification.

## Goal
A judge should understand in under 30 seconds:
1. What happened?
2. What failed?
3. What is the agent doing?
4. What evidence does it have?
5. What does it recommend?
6. Why?
7. Is it authorized?
8. Did it work?
9. What happened when verification failed?
10. Did it recover?

## Main dashboard
Build one investigation screen containing:
- header and mission status
- drone visualization
- telemetry
- mission/dependency graph
- agent investigation trace
- evidence
- hypotheses
- trust
- mission impact
- candidate actions
- simulation results
- policy/authorization
- execution
- verification
- recovery

Suggested layout:
```text
┌─────────────────────────────────────────────┐
│ AEGIS                         MISSION STATUS │
├───────────────────┬─────────────────────────┤
│ Drone + telemetry │ Mission dependency graph│
├───────────────────┴─────────────────────────┤
│ Agent investigation / tool trace            │
├─────────────────────────────────────────────┤
│ Evidence       │ Trust / Mission Impact     │
├─────────────────────────────────────────────┤
│ Candidate response simulations              │
├─────────────────────────────────────────────┤
│ Policy / Authorization / Execution / Verify │
└─────────────────────────────────────────────┘
```

## Technology
Use React + TypeScript + Tailwind. React Flow is appropriate for the dependency graph if already available.

Do not add complex frameworks unless they save time.

## Drone visualization
Use a clean 2D or lightweight 3D visualization. Show:
- position
- heading
- path
- mission route
- target
- fault state

When GPS fault activates, visibly mark GPS as degraded and show trajectory disagreement.

## Telemetry
Show:
```text
Position
Velocity
Heading
GPS Trust
IMU Trust
Mission Progress
Mission Status
```

Update live from the backend.

## Mission graph
Show:
GPS → Position Estimation → Navigation → Route Following → Mission Progress

When GPS fails, visually propagate the degraded state through dependent capabilities.

## Agent trace
Display real backend events, for example:
```text
✓ get_system_state()
✓ get_observations()
✓ get_trust()
✓ generate_hypotheses()
→ get_mission_impact()
```

Do not fake agent events in the frontend. Use backend events.

## Evidence
Show source and meaning:
```text
GPS residual: 8.4m
Source: GPS / IMU comparison

GPS trust: 0.31
Source: Trust engine

Mission risk: HIGH
Source: Mission impact engine
```

## Hypotheses
Show competing explanations with backend confidence:
```text
GPS integrity degradation    91%
Sensor noise                  6%
Inertial issue                3%
```

## Trust
Show:
```text
GPS     31%
IMU     92%
COMMS   98%
```
Make the relationship between GPS trust and mission risk visible.

## Mission impact
Show:
- severity
- affected capabilities
- navigation
- position estimation
- route following
- mission progress

## Candidate actions
Render actual backend simulation results:
```text
Continue GPS        HIGH RISK
Switch to Inertial  MEDIUM RISK  ← RECOMMENDED
Safe Mode            LOW RISK
```

Do not hard-code fake values after integration.

## Authorization
When policy requires human approval, show:
```text
ACTION REQUIRES AUTHORIZATION

Switch to Inertial Navigation
Mission Risk: MEDIUM
GPS Trust: 0.31
Expected Safety: 78%

[ APPROVE ] [ REJECT ]
```
Buttons must call the real backend.

## Execution
Show:
```text
✓ Policy approved
✓ Action authorized
→ Executing
→ Navigation mode: INERTIAL
```

## Verification failure
Make this a major visual moment:
```text
⚠ VERIFICATION FAILED

Reason:
Position residual remains above safe threshold.

AGENT REPLANNING...
```

Then show:
```text
NEW PLAN
1. Enter Safe Mode
2. Stabilize navigation
3. Verify mission state
```

## Recovery
Final state:
```text
✓ RECOVERY SUCCESSFUL
Navigation: SAFE_MODE
Mission Risk: LOW
Verification: PASSED
AEGIS STATUS: MISSION SAFETY RESTORED
```

## Demo mode
Create:
`[ RUN INCIDENT ]`

It should reliably trigger:
Reset → normal mission → GPS fault → agent → action → authorization → execution → verification failure → replan → recovery.

This must be repeatable.

## Do not build
Avoid:
- login
- user profiles
- mobile app
- multiple dashboards
- elaborate 3D
- PX4
- ROS2
- real drone control
- multiple incident types
- multi-agent UI
- excessive charts
- decorative animations

The UI communicates the agent. It is not the product itself.

## API integration
Consume:
```text
GET  /health
GET  /api/v1/state
GET  /api/v1/tools
POST /api/v1/reset
POST /api/v1/tick
POST /api/v1/scenario/gps-integrity
POST /api/v1/agent/run
```

Prefer WebSocket/SSE for live agent events if stable. Otherwise poll.

## Shared contracts
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

If a contract changes, coordinate with Person A before changing frontend logic.

## Timeline
9:00–10:00 UI shell
10:00–11:00 telemetry + simulator visualization
11:00 mentor
11:15–1:00 agent trace/evidence/hypotheses
1:00 break
2:00 mentor
2:15–3:00 action cards
3:00–4:00 simulation visualization
4:00 midpoint
4:00–5:00 policy/authorization
5:00–5:45 execution/verification
5:45–6:00 recovery preparation
6:00 final sprint
6:00–7:00 recovery flow
7:00–7:30 polish
7:30–8:00 production build/screenshots
8:00–9:00 video/deck/submission support

## Visual rules
Prioritize:
- information hierarchy
- readability
- state visibility
- agent transparency
- decision transparency

Avoid:
- excessive gradients
- tiny text
- overloaded dashboards
- decorative charts
- animations that hide state changes

## Demo video
Target 2–3 minutes:
0:00–0:15 normal mission
0:15–0:30 GPS fault
0:30–0:55 investigation
0:55–1:15 evidence/hypotheses/trust
1:15–1:35 simulation
1:35–1:50 policy/authorization
1:50–2:05 execution
2:05–2:20 verification failure
2:20–2:40 replanning
2:40–2:55 recovery
2:55–3:00 final result

Final screen:
**MISSION SAFETY RESTORED**

## Pitch deck
Exactly five slides:
1. Problem
2. Solution
3. Agent workflow / architecture
4. Demo + impact
5. Why AEGIS / scalability

## 4 PM checkpoint
Must show:
- drone moving
- GPS fault
- telemetry change
- agent trace
- evidence
- hypotheses
- trust
- mission risk
- candidate actions
- simulation results

If anything is missing, prioritize integration over visual polish.

## Definition of done
A judge can follow:
Something went wrong → AEGIS noticed → agent investigated → evidence supported a hypothesis → mission impact assessed → responses simulated → governed action selected → authorized → executed → verification failed → agent replanned → system recovered.
