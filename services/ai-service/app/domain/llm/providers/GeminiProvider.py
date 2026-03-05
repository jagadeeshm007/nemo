# ==============================================================================
# AI Service — Google Gemini Provider Implementation
# ==============================================================================

from __future__ import annotations

from typing import AsyncIterator

import google.generativeai as genai

from app.domain.llm.LLMProvider import (
    LLMProvider,
    LLMProviderConfig,
    CompletionResponse,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, config: LLMProviderConfig) -> None:
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self._models: dict[str, genai.GenerativeModel] = {}
        # Pre-initialize configured models
        for model_cfg in config.models:
            if model_cfg.enabled:
                self._models[model_cfg.id] = genai.GenerativeModel(model_cfg.id)
        logger.info("Gemini provider initialized")

    def _get_model(self, model_id: str) -> genai.GenerativeModel:
        if model_id not in self._models:
            self._models[model_id] = genai.GenerativeModel(model_id)
        return self._models[model_id]

    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        """Convert OpenAI-style messages to Gemini format."""
        system_instruction = None
        history = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        return system_instruction, history

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> CompletionResponse:
        gemini_model = self._get_model(model)
        system_instruction, history = self._convert_messages(messages)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Use last user message as the prompt
        last_message = history[-1]["parts"][0] if history else ""
        chat_history = history[:-1] if len(history) > 1 else []

        chat = gemini_model.start_chat(history=chat_history)
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
        )

        return CompletionResponse(
            content=response.text,
            model=model,
            provider="google",
            finish_reason="stop",
            prompt_tokens=0,  # Gemini doesn't always expose token counts
            completion_tokens=0,
            total_tokens=0,
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
        gemini_model = self._get_model(model)
        _, history = self._convert_messages(messages)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        last_message = history[-1]["parts"][0] if history else ""
        chat_history = history[:-1] if len(history) > 1 else []

        chat = gemini_model.start_chat(history=chat_history)
        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            text = [text]

        results = []
        for t in text:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=t,
            )
            results.append(result["embedding"])
        return results
