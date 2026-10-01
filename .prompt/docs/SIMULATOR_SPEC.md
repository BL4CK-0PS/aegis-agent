# Simulator Specification

## Purpose

The simulator provides a deterministic, reproducible environment for demonstrating the complete AEGIS loop without controlling a real physical system.

## State

```text
time
x, y
vx, vy
heading
navigation_mode
gps_trust
imu_trust
communication_health
energy
mission_progress
mission_status
gps_bias
gps_fault_active
```

## Normal behavior

The drone follows a predefined trajectory.

GPS and inertial/predicted position remain approximately consistent.

## GPS integrity scenario

At fault injection:
- GPS bias is introduced.
- GPS trust is reduced.
- mission status becomes degraded.
- subsequent ticks increase GPS bias.
- trust continues to decline.
- residual and anomaly score increase.

## Fault endpoint

```http
POST /api/v1/scenario/gps-integrity
```

## Time advancement

```http
POST /api/v1/tick
```

## State endpoint

```http
GET /api/v1/state
```

The response exposes:
- current state,
- predicted position,
- GPS position,
- residual,
- anomaly score.

## Determinism

The initial implementation uses a fixed random seed so the judge can reproduce the same incident.

## Deliberate verification failure

For the demo, one selected action path can be configured so that the first expected outcome is not achieved. This creates a visible transition:

**Execute → Verify failed → Recover → Replan**

The failure is controlled and deterministic, not an accidental demo catastrophe. Humanity has already invented live demos; there is no need to make them more dangerous.
