# Solution Overview

## AEGIS

AEGIS combines a deterministic computational core with an agentic orchestration layer.

### Core closed loop

**Observe → Estimate → Detect → Fuse → Trust → Assess → Simulate → Optimize → Authorize → Execute → Verify → Recover**

## Layer 1 — Environment

A deterministic simulator produces:
- vehicle state,
- GPS observation,
- inertial/predicted state,
- navigation mode,
- communication health,
- energy,
- mission progress,
- fault state.

## Layer 2 — Computational decision core

### State estimation
Produces a current state representation and residuals between observations and predicted state.

### Anomaly detection
Calculates an interpretable anomaly score from residuals and persistence.

### Evidence fusion
Combines telemetry and contextual evidence into incident hypotheses.

### Dynamic trust
Updates confidence in evidence sources such as GPS and IMU.

### Dependency graph
Represents relationships between components, capabilities, and mission objectives.

### Mission risk
Maps component conditions into mission-level consequences.

### Counterfactual simulation
Tests candidate actions before execution.

### Policy
Determines whether an action is allowed, denied, or requires human authorization.

### Execution
Applies a bounded action to the simulator.

### Verification
Compares expected and observed post-action state.

### Recovery
If verification fails, the system updates its state and starts a new decision cycle.

## Layer 3 — Agent

The agent does not replace the computational core.

It:
- receives a goal,
- plans an investigation,
- calls typed tools,
- observes structured outputs,
- chooses the next step,
- requests simulations,
- decides when enough evidence has been gathered,
- follows policy,
- reacts to verification results,
- replans.

## Key design property

The agent has autonomy over **workflow**, not unrestricted authority over **safety-critical state**.

This makes the system both more genuinely agentic and easier to reason about.
