# ==============================================================================
# AI Service — Anthropic (Claude) Provider Implementation
# ==============================================================================

from __future__ import annotations

from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.domain.llm.LLMProvider import (
    CompletionResponse,
    LLMProvider,
    LLMProviderConfig,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude Sonnet 4, Claude 3.5 Haiku, etc.)."""

    def __init__(self, config: LLMProviderConfig) -> None:
        super().__init__(config)
        self._client = AsyncAnthropic(
            api_key=config.api_key,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )
        logger.info("Anthropic provider initialized")

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        # Extract system message
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)

        params = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system:
            params["system"] = system
        if tools:
            params["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {}),
                }
                for t in tools
                if "function" in t
            ]

        response = await self._client.messages.create(**params)

        content = ""
        tool_calls = None
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "arguments": str(block.input),
                    }
                )

        return CompletionResponse(
            content=content,
            model=response.model,
            provider="anthropic",
            finish_reason=response.stop_reason or "end_turn",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)

        params = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }
        if system:
            params["system"] = system

        async with self._client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, text: str | list[str]) -> list[list[float]]:
        # Anthropic does not natively support embeddings.
        # Delegate to a different provider or raise.
        raise NotImplementedError(
            "Anthropic does not provide an embeddings API. "
            "Use OpenAI or another provider for embeddings."
        )
