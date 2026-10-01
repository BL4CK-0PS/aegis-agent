# Agent Workflow

## Agent goal

Example goal:

> Investigate the navigation-integrity incident and restore safe mission operation within the defined policy and safety constraints.

## State maintained by the agent

```text
incident_id
goal
current_step
observations
evidence
hypotheses
trust_snapshot
mission_impact
candidate_actions
simulation_results
policy_results
authorization_status
execution_result
verification_result
replan_count
```

## Tool contract

Every tool returns structured data. The agent is not allowed to invent telemetry or mutate protected state directly.

### 1. get_system_state

Returns:
- vehicle state,
- mission status,
- navigation mode,
- energy,
- progress.

### 2. get_observations

Returns:
- GPS observation,
- predicted/inertial position,
- residual,
- anomaly indicators,
- timestamps/provenance.

### 3. get_trust

Returns:
- GPS trust,
- IMU trust,
- communication trust,
- trust-change reasons.

### 4. get_dependency_graph

Returns:
- affected components,
- capabilities,
- mission objectives,
- dependency edges.

### 5. generate_hypotheses

Returns structured hypotheses such as:
- GPS integrity issue,
- inertial estimation issue,
- transient observation noise,
- mixed/uncertain condition.

### 6. simulate_action

Input:
```json
{
  "action": "switch_navigation_mode"
}
```

Returns:
- predicted mission outcome,
- predicted risk,
- energy impact,
- residual uncertainty,
- expected recovery time.

### 7. evaluate_policy

Checks:
- action validity,
- safety constraints,
- authorization requirement,
- reason.

### 8. execute_action

Executes only an approved bounded simulator action.

### 9. verify_action

Checks whether the observed post-action state matches expected conditions.

### 10. replan

Builds a new investigation/response path from the updated state.

## Example agent trace

```text
GOAL
  ↓
get_system_state
  ↓
get_observations
  ↓
get_trust
  ↓
generate_hypotheses
  ↓
get_dependency_graph
  ↓
simulate_action(A)
simulate_action(B)
  ↓
evaluate_policy(best_action)
  ↓
human authorization
  ↓
execute_action
  ↓
verify_action
  ↓
verification failed
  ↓
replan
  ↓
simulate alternative
  ↓
policy
  ↓
execute
  ↓
verify
```

## What makes this agentic

The sequence is not a fixed hard-coded pipeline.

The agent can decide:
- whether additional evidence is needed,
- which typed tool to call next,
- whether uncertainty warrants another hypothesis check,
- which candidate actions should be simulated,
- whether to stop investigation,
- whether to replan after an unexpected outcome.

The safety boundaries remain deterministic.
