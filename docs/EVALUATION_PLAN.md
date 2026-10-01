# Evaluation Plan

## Objective

Evaluate whether the integrated AEGIS loop provides more decision capability than simpler alerting or fixed-rule behavior in the controlled simulator.

## Baselines

### Baseline A — Alert-only

Detect and report the anomaly.

No response optimization.

### Baseline B — Fixed-rule

Detect the anomaly and apply a predefined response.

No counterfactual comparison.

### AEGIS

Estimate + evidence + trust + dependency graph + mission risk + simulation + governed execution + verification + recovery.

## Metrics

### Detection
- precision
- recall
- false-alarm rate

### Decision
- time from incident to recommendation
- number of tool calls
- number of replans
- policy escalation frequency

### Risk and mission
- estimated risk before/after action
- realized simulated risk
- mission progress preserved
- recovery time

### Robustness
- noisy observations
- missing observations
- conflicting observations

## Hackathon evaluation

The 12-hour demo should focus on reproducible behavior rather than claiming statistically significant scientific results.

A suitable demo table is:

| Stage | Observable result |
|---|---|
| Normal | stable state and mission progress |
| Fault | GPS residual increases |
| Detection | anomaly becomes visible |
| Investigation | agent gathers evidence |
| Trust | GPS trust decreases |
| Impact | navigation capability becomes affected |
| Simulation | candidate responses produce different predicted outcomes |
| Policy | action is allowed or escalated |
| HITL | authorization is visible |
| Execution | simulator state changes |
| Verification | expected outcome checked |
| Recovery | failed verification triggers replanning |

## Research evaluation later

The longer-term AEGIS project can evaluate multiple scenarios including communication degradation, component failure, security anomalies, and simultaneous disruptions. Those broader scenarios are outside the minimum Bharat Agentic demo scope.
