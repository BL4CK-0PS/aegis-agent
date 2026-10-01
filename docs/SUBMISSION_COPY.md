# Submission Copy

## Project Name

AEGIS

## Full Name

Autonomous Evidence-driven Governance and Intelligent Safety

## Tagline

Mission-aware agentic decision intelligence for autonomous systems.

## Problem Statement

Autonomous systems can detect abnormal observations, but detection alone does not determine what is happening, what evidence can be trusted, how the incident affects the mission, which response is safest, whether the response is permitted, or whether it actually worked.

AEGIS addresses this gap with a governed agentic decision loop.

## Solution Overview

AEGIS investigates uncertain autonomous-system incidents using a combination of structured telemetry, evidence fusion, dynamic trust, dependency analysis, mission-level risk assessment, counterfactual simulation, policy, human authorization, execution, verification, and recovery.

The agent plans and orchestrates the investigation through typed tools. The computational core remains authoritative for state, risk, policy, execution, and verification.

## Agent Workflow

Observe → Investigate → Gather Evidence → Form Hypotheses → Update Trust → Assess Mission Impact → Simulate Responses → Evaluate Policy → Authorize → Execute → Verify → Recover/Replan

## Technology Stack

- Python 3.12
- FastAPI
- Pydantic
- Deterministic simulator
- Structured agent/tool calling
- React + TypeScript
- WebSocket/SSE
- SQLite where persistence is required
- Docker

## Key Innovation

The project combines agentic workflow orchestration with a bounded computational decision loop.

The LLM is not treated as an unrestricted safety controller. Instead, it operates over typed tools and structured results while deterministic components enforce policy, execution, and verification.

## Demo Scenario

A simulated drone experiences GPS integrity degradation. AEGIS investigates the evidence, updates trust, evaluates mission impact, simulates responses, requests authorization, executes a bounded simulator action, verifies the outcome, and replans after a controlled verification failure.

## Safety

Simulator-only. No real-world control or offensive actions.

## Repository

`<GITHUB_REPOSITORY_URL>`

## Demo

`<LIVE_DEMO_URL_OR_LOCAL_INSTRUCTIONS>`

## Video

`<DEMO_VIDEO_URL>`

## Disclosure

AEGIS has a pre-existing research/specification foundation. The hackathon implementation is a new scoped implementation developed for this event and is disclosed accordingly.
