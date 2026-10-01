# Problem Statement

## Title

Mission-Aware Decision Support for Uncertain Autonomous-System Incidents

## Problem

Autonomous systems operate using observations that may be noisy, delayed, incomplete, contradictory, or unreliable. An anomaly detector can identify that something is wrong, but detection alone does not answer the operational questions that matter next:

- What is actually happening?
- Which evidence can still be trusted?
- Which competing explanations fit the observations?
- Which mission functions are affected?
- What actions are available?
- What could happen if each action is taken?
- Which actions are permitted by policy?
- Does the selected action actually work?
- What should happen if it fails?

This creates a gap between **detection** and **governed decision-making**.

## Example

A simulated autonomous drone reports a navigation anomaly:
- GPS position increasingly disagrees with inertial/predicted position.
- GPS trust should decrease as contradictory evidence accumulates.
- The navigation subsystem depends on multiple observations.
- Continuing normally may increase mission risk.
- Switching to an alternative navigation mode may reduce risk but affect mission performance.
- A response therefore needs investigation, simulation, policy checking, authorization, execution, and verification.

## Why an agent is useful

The investigation is not a single prediction.

The system must repeatedly:
1. inspect the current state,
2. decide which evidence to obtain,
3. interpret structured results,
4. determine whether uncertainty is sufficiently reduced,
5. simulate alternatives,
6. request authorization when necessary,
7. act,
8. inspect the outcome,
9. replan if the result differs from expectation.

That sequence is naturally expressed as an agentic workflow.

## Scope

For the hackathon:
- one simulated autonomous drone,
- one reproducible GPS-integrity incident,
- synthetic/controlled telemetry,
- bounded simulated actions,
- policy and human authorization,
- execution verification,
- recovery/replanning.

## Non-goals

AEGIS does not attempt to:
- control real physical assets,
- provide production safety certification,
- replace flight-control or mission-control systems,
- claim universal autonomous reasoning,
- make LLM-only safety-critical decisions.
