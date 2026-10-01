# Pre-existing Work and Originality Disclosure

## Pre-existing foundation

AEGIS existed before the Bharat Agentic 2026 hackathon as a research/project specification.

The pre-existing material includes:
- problem definition,
- mission-aware decision-intelligence concept,
- closed-loop architecture,
- computational module definitions,
- simulator concept,
- research questions,
- evaluation concepts,
- safety/non-goal definitions.

The earlier research architecture proposed Rust, React/TypeScript, and PostgreSQL, with modular computational components.

## Hackathon implementation

The Bharat Agentic implementation is a new scoped implementation built for the hackathon.

The hackathon version:
- uses Python/FastAPI,
- implements a smaller controlled simulator,
- introduces the agentic orchestration layer,
- implements typed tool calling,
- connects the agent to structured computational components,
- demonstrates policy/HITL,
- demonstrates execution verification,
- demonstrates recovery/replanning,
- provides a focused deterministic demo.

## Third-party technologies

The implementation may use open-source frameworks and libraries such as:
- Python
- FastAPI
- Pydantic
- React
- TypeScript
- Docker
- an agent/LLM SDK or compatible local model interface.

Third-party technologies remain subject to their respective licenses and terms.

## No false novelty claim

AEGIS does not claim that state estimation, anomaly detection, Bayesian reasoning, dependency graphs, simulation, optimization, policy enforcement, or LLM tool calling were individually invented by the team.

The intended contribution is the integration and demonstration of a mission-aware, uncertainty-aware, governed agentic workflow in a reproducible controlled environment.

## Judge disclosure

The team should explicitly state:

> AEGIS has a pre-existing research and specification foundation. We built a new, hackathon-scoped implementation during Bharat Agentic 2026, including the agentic orchestration, typed tools, controlled simulator integration, policy workflow, verification, and recovery loop demonstrated here.
