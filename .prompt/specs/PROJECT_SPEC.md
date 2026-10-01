# Project specification

## Identity
AEGIS = Autonomous Evidence-driven Governance and Intelligent Safety.
Tagline: Mission-aware agentic decision intelligence for autonomous systems.
Suggested domain: Developer & AI; confirm at mentor session.

## Goal
A single controlled simulated drone encounters GPS integrity degradation. An LLM agent must use actual typed tools to investigate telemetry disagreement, gather evidence, generate competing hypotheses, update trust, assess mission impact, simulate responses, obey a deterministic policy and human approval gate, execute a permitted simulated action, verify it, and replan after a deliberately induced verification failure.

## Agent flow
Understand → Reason → Plan → Use Tools → Act → Deliver.
Detailed: Observe → Evidence → Hypotheses → Trust → Mission Impact → Candidate Actions → Counterfactual Simulation → Policy → Authorization → Execution → Verification → Recovery.

## Tools
`get_system_state`, `get_observations`, `get_trust`, `generate_hypotheses`, `get_mission_impact`, `get_dependency_graph`, `generate_actions`, `simulate_action`, `evaluate_policy`, `execute_action`, `verify_action`, `replan`.

## Actions
`continue_gps`, `switch_inertial`, `safe_mode`. Do not execute `continue_gps` when GPS trust is below policy threshold. Human approval is mandatory for policy-gated actions. Never let the LLM mutate simulator state directly.

## Safety invariants
- All tool arguments validated with Pydantic or equivalent.
- Model can request actions, never override policy.
- Authorization is explicit, tied to action/incident, and checked on execution.
- Execution returns actual simulator state, not fabricated claims.
- Verification checks observed state and safety criteria, not LLM self-report.
- Limit tool iterations and guard against loops.
- Failure path must be deterministic and replayable for demo.
- No real drone, military or industrial actuator access.

## Non-goals
No ROS2, PX4, real drone, multi-agent, blockchain, custom training, massive RAG, additional scenarios, enterprise authentication, mobile app.

## Tech stack
Python 3.12, FastAPI, Pydantic, OpenAI-compatible tool-calling provider (e.g. configured Ollama endpoint), pytest/httpx, Docker; React, TypeScript, Tailwind. SQLite optional. SSE/WebSocket optional; polling fallback.

## Definition of done
Clean reset → fault → real LLM tool calls → evidence → risk → response simulations → policy → approval → simulated execution → verification failure → replanning → safe mode → verification success → structured incident report. Working API, frontend, Docker, GitHub, 2–3 min video, 5-slide deck and completed submission.
