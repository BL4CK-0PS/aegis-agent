# Safety and Governance

## Safety boundary

AEGIS is a simulator-only prototype.

It must not:
- control real drones or vehicles,
- issue real-world actuator commands,
- execute arbitrary shell commands,
- perform offensive cyber operations,
- bypass authorization,
- treat generated text as ground truth.

## LLM authority model

The LLM is an orchestration component.

It may:
- plan investigations,
- choose among exposed tools,
- interpret structured results,
- request simulations,
- summarize evidence,
- decide that more evidence is needed.

It may not independently:
- modify protected state,
- override policy,
- authorize itself,
- fabricate telemetry,
- directly command physical systems.

## Policy states

Every candidate action returns one of:

```text
ALLOW
DENY
REQUIRES_HUMAN_AUTHORIZATION
```

## Human-in-the-loop

High-impact actions are routed to an explicit authorization step.

The UI should show:
- action,
- reason,
- predicted risk,
- expected benefit,
- simulation result,
- policy decision.

The human authorization event is recorded.

## Audit trail

Record:
- timestamp,
- incident ID,
- agent step,
- tool call,
- tool arguments,
- structured result,
- selected hypothesis,
- candidate actions,
- simulation result,
- policy decision,
- authorization,
- execution,
- verification,
- recovery/replanning.

## Responsible AI

The project is designed around bounded autonomy, explicit constraints, reproducibility, and transparency rather than unrestricted autonomous control.
