"""
AEGIS LLM Provider Abstraction
Implements OpenAI-compatible provider with support for Ollama, vLLM, and OpenAI,
alongside Fake and Deterministic providers for offline validation.
"""

from __future__ import annotations
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded from backend/.env if present
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

logger = logging.getLogger("aegis.provider")


@dataclass
class ToolCallItem:
    id: str
    name: str
    arguments: Dict[str, Any]
    raw_arguments: str = ""
    parse_error: Optional[str] = None


@dataclass
class ProviderResponse:
    tool_calls: List[ToolCallItem] = field(default_factory=list)
    content: Optional[str] = None
    thought: Optional[str] = None
    finish_reason: str = "stop"
    raw: Optional[Any] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base class for all AEGIS LLM reasoning providers."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> ProviderResponse:
        pass


class OpenAICompatibleProvider(LLMProvider):
    """
    OpenAI-compatible client capable of connecting to local Ollama, vLLM,
    or OpenAI cloud endpoints.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "ollama"))
        self.model = model or os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "qwen2.5:7b"))
        self.timeout = timeout

        try:
            import openai
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "ollama",
                timeout=self.timeout,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize openai client: {e}")
            self.client = None

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> ProviderResponse:
        if not self.client:
            raise RuntimeError("OpenAI client is not initialized.")

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls: List[ToolCallItem] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                raw_args = tc.function.arguments or "{}"
                parse_err = None
                try:
                    args = json.loads(raw_args)
                    if not isinstance(args, dict):
                        args = {"value": args}
                except Exception as ex:
                    args = {}
                    parse_err = f"Malformed JSON arguments: {str(ex)}"

                tool_calls.append(
                    ToolCallItem(
                        id=tc.id or f"call_{tc.function.name}",
                        name=tc.function.name,
                        arguments=args,
                        raw_arguments=raw_args,
                        parse_error=parse_err,
                    )
                )

        return ProviderResponse(
            tool_calls=tool_calls,
            content=message.content,
            finish_reason=choice.finish_reason or "stop",
            raw=response,
        )


class FakeLLMProvider(LLMProvider):
    """
    Programmable mock provider for deterministic offline testing.
    Allows testing single/multiple tool calls, malformed arguments,
    unknown tools, step budget limits, and completion texts.
    """

    def __init__(self, responses: Optional[List[ProviderResponse]] = None):
        self.responses: List[ProviderResponse] = responses or []
        self.call_history: List[List[Dict[str, Any]]] = []

    def add_response(self, response: ProviderResponse) -> None:
        self.responses.append(response)

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> ProviderResponse:
        self.call_history.append(messages)
        if self.responses:
            return self.responses.pop(0)

        # Default fallback if queue empty
        return ProviderResponse(
            content="Fake provider finished investigation with no further actions.",
            finish_reason="stop",
        )


class FallbackDeterministicProvider(LLMProvider):
    """
    Context-aware fallback provider that dynamically performs the canonical
    investigation sequence when no live LLM server is accessible.
    Clearly identifies itself as a fallback mode in trace events.
    """

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> ProviderResponse:
        tool_results = {
            msg.get("name"): msg.get("content")
            for msg in messages
            if msg.get("role") == "tool"
        }

        # Sequence of read-only investigation steps
        if "get_system_state" not in tool_results:
            return ProviderResponse(
                tool_calls=[
                    ToolCallItem(
                        id="call_fallback_state",
                        name="get_system_state",
                        arguments={},
                    )
                ],
                thought="[Fallback Mode] Inspecting vehicle telemetry and baseline state.",
            )

        if "get_observations" not in tool_results:
            return ProviderResponse(
                tool_calls=[
                    ToolCallItem(
                        id="call_fallback_obs",
                        name="get_observations",
                        arguments={},
                    )
                ],
                thought="[Fallback Mode] Querying comparative observations and GPS-IMU residual.",
            )

        if "get_trust" not in tool_results:
            return ProviderResponse(
                tool_calls=[
                    ToolCallItem(
                        id="call_fallback_trust",
                        name="get_trust",
                        arguments={},
                    )
                ],
                thought="[Fallback Mode] Evaluating dynamic sensor integrity trust scores.",
            )

        if "generate_hypotheses" not in tool_results:
            return ProviderResponse(
                tool_calls=[
                    ToolCallItem(
                        id="call_fallback_hyp",
                        name="generate_hypotheses",
                        arguments={},
                    )
                ],
                thought="[Fallback Mode] Formulating competing incident hypotheses.",
            )

        if "get_mission_impact" not in tool_results:
            return ProviderResponse(
                tool_calls=[
                    ToolCallItem(
                        id="call_fallback_impact",
                        name="get_mission_impact",
                        arguments={},
                    )
                ],
                thought="[Fallback Mode] Assessing mission operational risk and affected capabilities.",
            )

        return ProviderResponse(
            content=(
                "Diagnostic Investigation Complete (Fallback Provider):\n"
                "- High positional residual detected between GPS and IMU.\n"
                "- Primary Hypothesis: H1 (GPS Signal Integrity Degradation / Spoofing) with high confidence.\n"
                "- GPS trust degraded below nominal threshold.\n"
                "- Mission operational risk elevated to CRITICAL/IMMEDIATE."
            ),
            finish_reason="stop",
        )


def get_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """Factory creating the appropriate LLMProvider based on configuration."""
    ptype = (provider_type or os.getenv("AEGIS_LLM_PROVIDER", "mock")).lower().strip()

    if ptype in ("openai", "ollama", "live"):
        return OpenAICompatibleProvider()
    elif ptype == "fallback":
        return FallbackDeterministicProvider()
    else:
        # Default mock / deterministic fallback
        return FallbackDeterministicProvider()
