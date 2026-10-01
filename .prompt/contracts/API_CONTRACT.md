# Shared API contract (proposed, freeze jointly)

This contract is a target, not a claim that existing endpoints already match. Person A should adapt existing responses or add a frontend-facing adapter. Person B must not assume unimplemented endpoints work.

## Endpoints
- `GET /health` (also keep existing `/api/v1/health`)
- `GET /api/v1/state`
- `POST /api/v1/reset`
- `POST /api/v1/tick`
- `POST /api/v1/scenario/gps-integrity`
- `GET /api/v1/tools`
- `POST /api/v1/agent/investigate` deterministic baseline
- `POST /api/v1/agent/run` actual LLM tool-calling agent
- `GET /api/v1/agent/{agent_id}` for run status/events if async
- `POST /api/v1/actions/{action_id}/authorize` approve/reject action (must validate incident and pending request)

## Example state
```json
{"time":12.0,"position":{"x":120.5,"y":84.2},"velocity":{"x":10.2,"y":5.1},"navigation_mode":"GPS_ASSISTED","gps_trust":0.31,"imu_trust":0.92,"mission_progress":0.42,"mission_status":"DEGRADED","gps_fault_active":true}
```

## Agent input
```json
{"goal":"Investigate the GPS navigation-integrity incident and restore safe mission operation within policy."}
```

## Agent response (example shape)
```json
{"agent_id":"agent-1234","status":"AWAITING_AUTHORIZATION","goal":"Investigate navigation integrity","steps":[{"step":1,"tool":"get_observations","status":"COMPLETED","summary":"GPS/IMU residual detected"}],"evidence":[],"hypotheses":[],"trust":{},"mission_impact":{},"candidate_actions":[],"simulation_results":[],"recommended_action":"switch_inertial","policy_result":{"decision":"REQUIRE_APPROVAL","reason":"Risk threshold exceeded"},"authorization":{"status":"PENDING","action_id":"act-1"},"execution_result":null,"verification_result":null,"replan_count":0}
```

## Approval request
```json
{"decision":"APPROVE","incident_id":"incident-1"}
```

## Agent event
```json
{"step":4,"tool":"get_trust","status":"COMPLETED","summary":"GPS trust degraded"}
```

## Action simulation
```json
{"id":"switch_inertial","name":"Switch to Inertial Navigation","risk":0.42,"mission_continuity":0.71,"risk_basis":"deterministic heuristic"}
```

## Verification
```json
{"verified":false,"reason":"Navigation residual remains above threshold","next_action_required":true}
```

## Notes
- JSON examples are illustrative, not actual measured output.
- Agree on casing and naming (`NORMAL`/`DEGRADED`/`CRITICAL`, `GPS_ASSISTED`/`INERTIAL`/`SAFE_MODE`).
- Agent may pause at approval; backend owns continuation.
- Return meaningful HTTP error codes; ensure idempotent reset and approval validation.
- If live streaming fails, poll run status.
