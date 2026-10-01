# Person A: Next Implementation Prompt — Real LLM Tool Calling

Implement the next milestone in the existing AEGIS Python FastAPI backend. **First inspect current code**, especially `app/tools/registry.py`, `app/agent/state.py`, `app/agent/runtime.py`, `app/core/models.py`, `app/main.py` and existing tests.

## Requirements
1. Add `openai` to backend requirements, and a provider abstraction in `app/agent/provider.py` using an OpenAI-compatible API with configurable `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (defaults may target local Ollama, e.g. `http://localhost:11434/v1`). Do not commit credentials. Environment configuration must actually be loaded from process environment (a `.env.example` file does not automatically load `.env`).
2. Expose registered read-only investigation tools to the model as function/tool definitions with correct JSON schemas. Keep the existing registry execute signature or update all call sites consistently.
3. Add `app/agent/llm_runtime.py`: bounded model→tool→model loop. Validate tool name and JSON object arguments, return tool results with matching tool-call IDs, support multiple tool calls in a single response, capture actual tool names/inputs/results/status in trace, and return final model conclusion plus trace. Limit both model rounds and total tool invocations; prevent infinite loops.
4. Convert dataclasses and Pydantic outputs to JSON safely. Keep errors sanitized in public API; record diagnostic details in logs. Treat untrusted tool/model output as data, not authority.
5. Register `POST /api/v1/agent/run` with stable request/response schemas. Preserve deterministic `/api/v1/agent/investigate` as clearly labeled fallback. Use a lock or per-run state to avoid simultaneous requests corrupting global simulator state; use sensible timeouts.
6. Do not expose policy/execution tools until deterministic policy and authorization checks exist. LLM may not bypass authorization or directly modify simulator state.
7. Add offline unit tests with a fake provider to prove: model selects a real tool, result goes back to model, multiple calls work, unknown tool rejected, malformed arguments rejected, budget enforced, final conclusion preserved, trace accurate. Run existing tests.
8. Show curl/PowerShell invocation for reset → fault → run. Clearly distinguish example output from verified output.

## Definition of done
A real model can investigate the GPS fault using typed tools, and the API returns its conclusion and genuine tool trace. Existing deterministic tests still pass. No fabricated execution or safety claims.
