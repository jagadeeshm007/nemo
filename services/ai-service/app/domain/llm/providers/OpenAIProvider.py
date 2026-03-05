# ==============================================================================
# AI Service — OpenAI Provider Implementation
# ==============================================================================

from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.domain.llm.LLMProvider import (
    CompletionResponse,
    LLMProvider,
    LLMProviderConfig,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4o-mini, o1, etc.)."""

    def __init__(self, config: LLMProviderConfig) -> None:
        super().__init__(config)
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )
        logger.info("OpenAI provider initialized")

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**params)
        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in choice.message.tool_calls
            ]

        return CompletionResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            finish_reason=choice.finish_reason or "stop",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
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
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        stream = await self._client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            text = [text]

        response = await self._client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return [item.embedding for item in response.data]
