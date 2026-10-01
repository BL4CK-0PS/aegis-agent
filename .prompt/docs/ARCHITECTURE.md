# Architecture

## High-level architecture

```text
                 ┌─────────────────────────┐
                 │   Operator / Judge UI    │
                 └────────────┬────────────┘
                              │
                       WebSocket / HTTP
                              │
                 ┌────────────▼────────────┐
                 │      AEGIS API           │
                 │        FastAPI           │
                 └────────────┬────────────┘
                              │
              ┌───────────────▼────────────────┐
              │      Agent Orchestrator         │
              │ plan → tools → inspect → replan │
              └───────────────┬────────────────┘
                              │ typed tools
       ┌──────────────────────┼────────────────────────┐
       │                      │                        │
┌──────▼──────┐       ┌───────▼────────┐       ┌──────▼──────┐
│ Evidence    │       │ Decision Core   │       │ Simulator   │
│ / Hypotheses│       │ trust/risk/etc. │       │ + faults    │
└─────────────┘       └───────┬────────┘       └─────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Policy / HITL     │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Execution Adapter │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Verification /    │
                    │ Recovery          │
                    └───────────────────┘
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| Simulator | Deterministic environment and fault injection |
| State estimator | Current state and residuals |
| Detector | Anomaly identification |
| Evidence engine | Structured evidence and hypotheses |
| Trust engine | Confidence updates |
| Graph engine | Dependency propagation |
| Risk engine | Mission-level impact |
| Simulation engine | Counterfactual action outcomes |
| Policy engine | Governance and authorization |
| Execution adapter | Bounded simulator actions |
| Verifier | Post-action validation |
| Recovery | Replanning |
| Agent | Workflow orchestration |
| UI | Human visibility and authorization |

## Data principle

The LLM should receive structured state and structured tool outputs rather than raw uncontrolled application internals.

## Failure containment

If the model:
- hallucinates a tool argument,
- proposes an unsupported action,
- requests an invalid action,
- attempts to bypass policy,

the typed tool layer rejects the request.

The application remains authoritative.
