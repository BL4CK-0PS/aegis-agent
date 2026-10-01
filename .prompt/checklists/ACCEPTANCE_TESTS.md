# Acceptance and demo tests

## Baseline
- [ ] `pytest -q` passes (record actual count).
- [ ] Health responds.
- [ ] Reset yields normal GPS-assisted state.
- [ ] Fault injection changes GPS bias/trust and residual.
- [ ] Deterministic investigation returns structured evidence and hypothesis.

## Agent
- [ ] Model actually selects tools (not pre-scripted trace).
- [ ] Registry executes real tools and returns structured results.
- [ ] Unknown/malformed tool calls fail safely.
- [ ] Iteration cap prevents infinite loops.
- [ ] Provider unavailable produces honest error/fallback clearly marked.

## Governed actions
- [ ] At least three candidate actions simulated.
- [ ] Policy rejects unsafe GPS continuation under low trust.
- [ ] Human approval request appears for gated action.
- [ ] Action cannot execute without matching authorization.
- [ ] Execution updates authoritative simulator state.
- [ ] Verification checks actual state.
- [ ] Demo-only injected verification failure triggers real replan.
- [ ] Safe-mode recovery verifies successfully.

## Frontend
- [ ] Live telemetry is not hardcoded.
- [ ] Real tool trace is visible.
- [ ] Approve/Reject invoke backend.
- [ ] Clean reset and repeated incident run work.
- [ ] `npm run build` passes.

## Submission
- [ ] Docker build and run tested.
- [ ] Hosted API accessible if API method chosen.
- [ ] Manifest matches official guide if YAML method chosen.
- [ ] GitHub pushed; README, setup, disclosures and `.env.example` included.
- [ ] 2–3 minute demo video recorded.
- [ ] Exactly 5 slides prepared.
- [ ] Official form submitted and confirmation captured before 9 PM.
