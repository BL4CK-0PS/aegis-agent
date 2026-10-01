# Technical Defense / Judge Q&A

## What makes this agentic?

The agent performs a multi-step investigation using typed tools, maintains state, decides what evidence to inspect next, requests counterfactual simulations, follows policy, observes execution results, and replans after verification failure.

It is not merely generating text.

## Why not let the LLM make the final decision?

Because the project deliberately separates probabilistic language reasoning from authoritative safety constraints. The LLM is useful for orchestration, but protected state, policy, authorization, execution, and verification remain explicit computational components.

## What is actually new?

The project does not claim novelty for individual algorithms. The intended contribution is the integrated closed loop connecting evidence, trust, mission impact, simulation, governance, execution, and verification under an agentic workflow.

## Why a simulator?

It gives reproducibility and safety. Every judge can observe the same controlled incident without connecting the system to a real autonomous platform.

## Why only one scenario?

The hackathon is 12 hours. A complete closed loop in one deterministic scenario is more defensible than five incomplete scenarios.

## How does the agent avoid hallucinating?

Tool outputs are structured. Tools validate inputs. Protected operations are enforced outside the LLM. Unsupported actions are rejected.

## Can the agent bypass policy?

No. Policy is an application-level gate. The agent can request an action, but the policy layer decides whether it is allowed, denied, or requires human authorization.

## What happens when execution fails?

The verifier marks the expected outcome as failed. Recovery updates the decision state and the agent starts another investigation/response cycle.

## How do you evaluate it?

The longer-term research plan compares AEGIS with alert-only and fixed-rule baselines under controlled scenarios. The hackathon demo focuses on visibly demonstrating the full closed loop rather than making unsupported statistical claims.

## What are the limitations?

- simulator fidelity limits external validity,
- trust is a model output, not truth,
- dependency graphs may omit unmodeled dependencies,
- simulation quality depends on disturbance assumptions,
- human authorization adds latency,
- LLM explanations can be wrong.

## Is this production-ready?

No. It is a controlled prototype and should not be presented as certified autonomous safety infrastructure.
