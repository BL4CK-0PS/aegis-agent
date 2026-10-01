# MASTER PROMPT | PERSON A | Antigravity

You are a senior Python/FastAPI agent systems engineer. Implement AEGIS backend in the CURRENT repository. **Inspect the repository first. Do not assume files exist, overwrite working code, or silently invent interfaces.** Read `specs/PROJECT_SPEC.md`, `contracts/API_CONTRACT.md`, `checklists/TIMELINE.md` and `checklists/ACCEPTANCE_TESTS.md` before edits.

## Ownership
You own backend/app/core, tools, agent, policy, action simulation, execution, verification, recovery, tests, Docker and API submission packaging. Person B owns React and visuals. Treat simulator state as one authoritative backend instance. Coordinate simulator data requirements through the API contract.

## Existing intended code
`app/main.py`; `app/core/{models,simulator,trust,evidence,risk}.py`; `app/tools/{context,registry,state_tools,analysis_tools}.py`; `app/agent/{state,planner,runtime}.py`; tests. Current deterministic planner lists five investigation tools; preserve it as a test fallback while implementing REAL LLM tool selection.

## Phase 1 | Inspect + baseline
1. Show file tree and summarize existing contracts.
2. Run `pytest -q`, report actual failures. Fix only needed compatibility bugs.
3. Confirm reset, GPS fault, tick, state and deterministic investigation endpoints.
4. Ensure state is consistent across tools and requests.

## Phase 2 | LLM tool calling
1. Add OpenAI-compatible provider configured by environment variables `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (defaults for local Ollama may be `http://localhost:11434/v1`, `ollama`, `qwen3:8b`; verify model actually installed).
2. Convert registry metadata to provider-compatible function schemas.
3. Implement multi-turn tool-calling loop: model chooses tool, validate JSON and schema, execute allowlisted tool, return structured tool result to model, repeat until conclusion. Do not hardcode a fake sequence.
4. Capture full event trace: step, tool, validated arguments, result summary, status, timestamps or sequence order, errors.
5. Cap iterations (e.g. 15), tool calls and timeouts. Reject malformed/unknown calls safely.
6. Expose `POST /api/v1/agent/run`. Preserve `/api/v1/agent/investigate` as deterministic fallback for testing.
7. Keep final response grounded in tool results. Add mock-provider tests without external model calls.

## Phase 3 | Decision + action tools
1. Add `get_dependency_graph`, `generate_actions`, `simulate_action` with deterministic counterfactual scores derived from current state. Clearly label heuristic estimates, not empirically measured probabilities.
2. Add `evaluate_policy`, `authorize_action`, `execute_action`, `verify_action`, `replan`. Authorization is a backend API operation, not a tool the LLM can self-approve. The agent may pause and return `AWAITING_AUTHORIZATION`, then resume after user approval.
3. Implement action identity and authorization binding; prevent executing unapproved/denied/stale actions.
4. Demonstrate inertial-switch verification failure followed by agent re-evaluation and safe-mode recovery, using an explicit demo-only failure-injection flag, never deceptive claims.
5. Tests: denied unsafe GPS action, approval required, no mutation without approval, successful safe mode, failed verification and recovery.

## Phase 4 | Integration + packaging
1. Implement stable REST JSON according to `contracts/API_CONTRACT.md`; prefer incremental agent events via polling; streaming optional.
2. CORS configured for local frontend; never expose secrets.
3. Docker build and run with health check. Note that Dockerized Ollama base URL cannot use localhost for host Ollama unless network setup supports it; document host address configuration.
4. Write `.env.example`, reproducible README and source disclosure.
5. **Do not invent official aiKart `agent.yaml` keys**; request manifest guide, or prepare hosted API submission path. Test actual entrypoint contract after guide arrives.
6. Run tests, smoke API calls, Docker test, and report what was genuinely verified.

## Deliverable format after each implementation stage
Provide: changed files, full runnable commands, test output, API sample requests/responses, blockers, and next smallest task. Implement code rather than only describing it. Avoid frontend edits.

## Hard constraints
No real drone control, no autonomous high-risk actuation, no policy bypass, no simulated fake LLM calls presented as real. No extra features until one end-to-end scenario passes.
