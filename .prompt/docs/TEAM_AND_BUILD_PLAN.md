# Team and Build Plan

## Team

Two-person implementation team.

## Person A — Agent + Backend + Decision Core

Responsibilities:
- FastAPI backend
- domain models
- simulator integration
- typed tool registry
- agent runtime
- investigation state
- evidence/hypothesis engine
- trust
- dependency graph
- risk
- policy/HITL
- execution/verification/replanning
- backend tests

## Person B — Simulator + Frontend

Responsibilities:
- simulator behavior
- scenario controls
- React interface
- telemetry visualization
- mission/dependency graph
- agent trace
- simulation result view
- policy/HITL panel
- verification/recovery visualization
- demo-mode controls

## Integration checkpoints

| Time | Target |
|---|---|
| T+2h | Simulator + API + initial UI |
| T+4h | Anomaly visible |
| T+6h | Agent calls at least 3 real tools |
| T+8h | Simulation → policy → authorization → execution |
| T+10h | Verification + replanning |
| T+11h | Demo freeze |
| T+12h | Submission |

## Cut order if behind schedule

Cut:
1. extra scenarios
2. advanced optimizer
3. persistence beyond essentials
4. secondary visualizations
5. advanced trust calibration

Do not cut:
- real agent tool calling
- simulator
- policy gate
- execution
- verification
- replanning

## Engineering principle

Build the smallest complete closed loop before adding features.

A beautiful dashboard around a half-built agent is still a half-built agent, which is a particularly decorative form of failure.
