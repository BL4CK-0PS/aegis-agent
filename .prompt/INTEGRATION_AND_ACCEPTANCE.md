# Integration Contract and Acceptance Tests

## Single source of truth
The Python backend owns authoritative simulator state and state transitions. Person B may build visualization/mock data locally but must not run a competing production simulator.

## Existing baseline endpoints (inspect actual implementation)
- `GET /api/v1/health`
- `GET /api/v1/state`
- `POST /api/v1/reset`
- `POST /api/v1/tick`
- `POST /api/v1/scenario/gps-integrity`
- `GET /api/v1/tools`
- `POST /api/v1/agent/investigate`

## Proposed new endpoints (implement and coordinate)
- `POST /api/v1/agent/run`
- Authorization endpoint, with action/run identifier and approve/reject state; choose exact path with Person B before implementation.
- Optional agent event stream; polling is acceptable if SSE/WebSocket threatens reliability.

## Canonical UI DTOs (target contract, NOT necessarily current responses)

### State
```json
{"time":12.0,"position":{"x":120.5,"y":84.2},"velocity":{"x":10.2,"y":5.1},"navigation_mode":"GPS_ASSISTED","gps_trust":0.31,"imu_trust":0.92,"mission_progress":0.42,"mission_status":"DEGRADED"}
```
### Agent trace
```json
{"step":4,"tool":"get_trust","status":"completed","summary":"GPS trust decreased due to persistent residual."}
```
### Action
```json
{"id":"switch_inertial","name":"Switch to Inertial Navigation","risk":0.42,"mission_continuity":0.71}
```
### Verification
```json
{"verified":false,"reason":"Navigation residual remains above threshold.","next_action_required":true}
```
Example values above are **illustrative**. Make sure backend and frontend use the same actual schema; no hidden field renames.

## Test scenarios
1. Reset: healthy GPS and mission status normal.
2. Inject GPS fault: observations diverge, anomaly grows, trust decreases, mission impact is meaningful.
3. Investigation: actual agent requests real tools; evidence/hypotheses are from tool results.
4. Candidate simulation: compare continue GPS, inertial, safe mode without changing live state.
5. Policy: unsafe GPS continuation denied; required approval cannot be bypassed.
6. Execution: only authorized action mutates simulator.
7. Verification: outcome checked against observed state, not agent prose.
8. Recovery: deliberately fail verification for inertial switch; replan to safe mode; verify success.
9. Reset and repeat: demo is deterministic and repeatable.
10. Container/API: build, run, health, run endpoint and UI integration verified.

## Integration discipline
- Publish exact schema and a sample API response before frontend integration.
- CORS configured only for expected demo frontend origins.
- Never log or expose model API secrets.
- Do not claim safety certification or production autonomous control.
