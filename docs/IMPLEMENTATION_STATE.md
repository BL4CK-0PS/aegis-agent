# Implementation State

## Completed

- FastAPI scaffold
- deterministic drone simulator
- GPS integrity fault injection
- state model
- observation model
- residual calculation
- anomaly score
- evidence model
- competing hypotheses
- dynamic GPS trust degradation
- reset endpoint
- API tests
- Dockerfile

## Not yet implemented

- typed agent tool registry
- LLM integration
- dependency graph
- mission risk engine
- counterfactual action simulation
- policy/HITL
- execution adapter
- verification
- recovery/replanning
- frontend
- judge-mode UI

## Definition of done for this milestone

The GPS fault must produce a reproducible chain:

GPS fault
→ residual increase
→ anomaly increase
→ evidence
→ competing hypotheses
→ GPS trust decrease
→ degraded/critical mission state
