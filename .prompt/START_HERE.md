# AEGIS | Bharat Agentic 2026 | Antigravity Workspace

**Start here.** This package contains **instructions and reference artifacts**, not a claim that the full project is already implemented. The starter/core ZIPs are historical reference implementations, not a substitute for inspecting the live repository.

## How to use with Antigravity

1. Extract this archive into a separate workspace or a documentation folder next to your real AEGIS repository. Do not overwrite your existing code with the reference ZIPs.
2. Open the actual repository in Antigravity. Ask it to read `START_HERE.md`, `ANTIGRAVITY_MASTER_PROMPT.md`, and `prompts/PERSON_A_BUILD_PROMPT.md` (or `PERSON_B_BUILD_PROMPT.md`).
3. Have it inspect the real code, show an implementation gap analysis, then implement the smallest working vertical slice. **Do not assume prior files exist until inspected.**
4. Person A and B work in separate branches/worktrees. Coordinate API contracts before integration.
5. Use `docs/` for product and safety context. Treat example numbers as illustrative, not test assertions.
6. Confirm the official aiKart Agent Manifest schema from the official guide; no schema has been provided in these materials. Do not invent `agent.yaml` fields.

## Roles
- **A:** backend, agent, tools, policy, execution, verification, tests, Docker, agent submission.
- **B:** simulator visualization and UI, telemetry, mission graph, authorization interface, demo, video, five-slide deck. Simulator ownership overlaps with an earlier A starter implementation: coordinate on a **single authoritative backend simulator**, not competing implementations.

## Critical deadline
Website says **9:00 PM final submission** on 1 Oct. Earlier email/guidelines mention **10:00 PM submission acceptance**, so use 9:00 PM as the safe hard deadline and confirm with organizers. Website lists winners **2 Oct 6:00 PM**; another email says **3 Oct 6:00 PM**. Confirm the result date separately.

## Read order
1. `ANTIGRAVITY_MASTER_PROMPT.md`
2. `prompts/PERSON_A_BUILD_PROMPT.md` or `prompts/PERSON_B_BUILD_PROMPT.md`
3. `INTEGRATION_AND_ACCEPTANCE.md`
4. `docs/ARCHITECTURE.md`, `docs/API_AND_TOOL_CONTRACTS.md`, `docs/SAFETY_AND_GOVERNANCE.md`
5. `submission/SUBMISSION_CHECKLIST.md`

## No false claims
Report which tests were actually run. A generated implementation is not automatically a working implementation. Never fabricate LLM tool calls, authorization, verification or benchmark results.
