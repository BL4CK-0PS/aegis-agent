# 2–3 Minute Demo Script

## 0:00–0:15 — Normal mission

Show:
- simulated drone state,
- mission progress,
- healthy navigation,
- stable trust.

Narration:

> AEGIS is a mission-aware agentic decision layer for autonomous systems. It does not simply detect anomalies. It investigates them, evaluates responses, governs execution, and verifies the result.

## 0:15–0:30 — Inject GPS incident

Trigger:

`GPS INTEGRITY FAULT`

Show:
- GPS bias,
- residual increase,
- anomaly score,
- trust degradation.

Narration:

> The drone's GPS observations are now inconsistent with the predicted navigation state.

## 0:30–0:55 — Agent investigates

Show agent trace:

```text
get_system_state
get_observations
get_trust
generate_hypotheses
get_dependency_graph
```

Narration:

> Instead of jumping directly to an action, the agent investigates the incident through typed tools and maintains structured state.

## 0:55–1:20 — Mission impact

Show:
- competing hypotheses,
- GPS trust,
- affected navigation dependency,
- mission risk.

Narration:

> The system separates evidence from assumptions. Trust changes as contradictory evidence accumulates, and the dependency graph maps the local navigation issue to mission-level impact.

## 1:20–1:45 — Counterfactual simulation

Show two candidate actions and their predicted outcomes.

Narration:

> AEGIS does not blindly execute the first plausible response. It simulates candidate actions and compares their expected consequences.

## 1:45–2:00 — Policy and authorization

Show:

`REQUIRES_HUMAN_AUTHORIZATION`

Narration:

> The agent can recommend an action, but policy remains authoritative. High-impact actions require explicit authorization.

## 2:00–2:20 — Execute and verify

Show:
- authorization,
- action execution,
- updated simulator state,
- verification.

Narration:

> The action is executed only inside the controlled simulator. The verifier then checks whether reality matches the predicted outcome.

## 2:20–2:45 — Deliberate failure

Show:

`VERIFICATION FAILED`

Narration:

> Now we deliberately make the first response fail verification.

## 2:45–3:00 — Recovery

Show:

`RECOVER → REPLAN → SIMULATE → AUTHORIZE → EXECUTE → VERIFY`

Narration:

> The important part is what happens next. AEGIS does not stop at failure. It updates the situation, replans, evaluates another response, and closes the loop.

Final line:

> AEGIS connects evidence, trust, mission impact, simulation, governance, execution, and verification into a closed decision loop.
