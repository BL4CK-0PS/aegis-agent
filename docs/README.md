# AEGIS — Bharat Agentic 2026

**Autonomous Evidence-driven Governance and Intelligent Safety**

> Mission-aware agentic decision intelligence for autonomous systems.

## 1. One-line pitch

AEGIS is a mission-aware agentic decision-intelligence system that investigates uncertain autonomous-system incidents, evaluates possible responses through simulation, and executes governed actions with verification and recovery.

## 2. Hackathon scope

Bharat Agentic 2026 is a 12-hour online Agentic AI hackathon. The project must demonstrate meaningful agentic behavior rather than a basic chatbot or wrapper. AEGIS therefore uses an agent that plans an investigation, selects typed tools, evaluates intermediate results, chooses when more evidence or simulation is required, passes actions through policy, and replans after verification failure.

## 3. Demonstration scenario

The demo uses one controlled simulated autonomous drone.

Normal mission:
- The drone follows a predefined mission.
- Navigation state is estimated from simulated observations.

Injected incident:
- GPS observations develop an abnormal bias.
- GPS-derived position diverges from inertial/predicted state.
- The anomaly increases as the incident persists.

AEGIS then:
1. observes the incident,
2. investigates available evidence,
3. forms competing hypotheses,
4. updates trust,
5. determines mission impact,
6. evaluates candidate responses,
7. applies policy,
8. requests human authorization where required,
9. executes the selected simulated action,
10. verifies the outcome,
11. recovers and replans if verification fails.

## 4. Safety boundary

AEGIS is simulator-only for this hackathon. It does not control a real drone, aircraft, vehicle, weapon, or other physical system.

The LLM is not the safety authority. It can orchestrate investigation and interpret structured results, but protected state, risk, policy, authorization, execution, and verification remain deterministic application components.

## 5. Repository structure

```text
aegis/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── simulator.py
│   │   └── tools/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
├── docs/
└── README.md
```

## 6. Intended technology stack

- Python 3.12
- FastAPI
- Pydantic
- Deterministic Python simulator
- Agent runtime with structured tool calling
- React + TypeScript for the operator UI
- WebSocket/SSE for live investigation traces
- Optional SQLite for local persistence
- Docker for reproducible execution

## 7. Design principle

The system separates:

**Agentic orchestration**
- planning
- tool selection
- evidence gathering
- hypothesis investigation
- deciding what to inspect next
- simulation requests
- replanning

from:

**Authoritative computational components**
- state
- anomaly score
- trust
- risk
- policy
- authorization
- execution
- verification

This separation is deliberate. The project should demonstrate useful autonomy without pretending that an LLM is a certified safety controller.

## 8. Current implementation target

The minimum viable demo is one deterministic GPS-integrity incident with:
- real typed tools,
- real agent tool calls,
- structured evidence,
- trust update,
- mission impact,
- candidate-action simulation,
- policy/HITL,
- simulated execution,
- verification,
- recovery/replanning,
- visible agent trace.

## 9. What is not being built

- real drone control
- real-world cyber operations
- unrestricted shell/tool access
- drone swarm
- multi-domain autonomy
- custom foundation-model training
- giant RAG pipeline
- multi-agent swarm
- enterprise SIEM replacement
- production safety certification

## 10. Disclosure

AEGIS has a pre-existing research/specification foundation created before this hackathon. The hackathon implementation is a new, explicitly scoped implementation built during the event. The hackathon implementation uses Python and a smaller controlled simulator rather than the longer-term Rust/React/PostgreSQL research architecture.

See `DISCLOSURE.md`.
