# ==============================================================================
# AI Service — LLM Provider Interface (Abstract Base)
# ==============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""
    id: str
    display_name: str = ""
    enabled: bool = True
    max_tokens: int = 4096
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    display_name: str = ""
    enabled: bool = False
    api_key: str = ""
    base_url: str = ""
    timeout_seconds: int = 120
    max_retries: int = 3
    models: list[ModelConfig] = field(default_factory=list)


@dataclass
class CompletionResponse:
    """Standardized completion response across providers."""
    content: str
    model: str
    provider: str
    finish_reason: str = "stop"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_calls: list[dict] | None = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class.
    This ensures a consistent interface across OpenAI, Anthropic, Google, etc.
    """

    def __init__(self, config: LLMProviderConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def config(self) -> LLMProviderConfig:
        return self._config

    def get_model_config(self, model_id: str) -> ModelConfig | None:
        """Find model configuration by ID."""
        for model in self._config.models:
            if model.id == model_id:
                return model
        return None

    def list_models(self) -> list[ModelConfig]:
        """Return all configured models for this provider."""
        return [m for m in self._config.models if m.enabled]

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        """
        Send a completion request and return the full response.

        Args:
            model: The model ID to use.
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (0.0 - 2.0).
            max_tokens: Maximum tokens to generate.
            tools: Optional list of tool definitions for function calling.

        Returns:
            CompletionResponse with the model's output.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a completion response, yielding text chunks.

        Args:
            model: The model ID to use.
            messages: List of message dicts.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            tools: Optional tool definitions.

        Yields:
            String chunks of the response.
        """
        ...

    @abstractmethod
    async def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings for the given text(s).

        Args:
            text: A single string or list of strings.

        Returns:
            List of embedding vectors.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the provider is reachable and operational."""
        try:
            response = await self.complete(
                model=self.list_models()[0].id if self.list_models() else "",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(response.content)
        except Exception:
            return False
