# ==============================================================================
# AI Service — Chat Routes
# ==============================================================================

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.domain.llm.LLMFactory import LLMFactory
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    model_provider: str = "openai"
    model_id: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int | None = None
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    model: str
    provider: str
    finish_reason: str
    usage: dict


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Send a chat message and receive a complete response."""
    llm_factory: LLMFactory = request.app.state.llm_factory

    messages = []
    if body.system_prompt:
        messages.append({"role": "system", "content": body.system_prompt})
    messages.append({"role": "user", "content": body.message})

    try:
        response = await llm_factory.complete(
            provider=body.model_provider,
            model=body.model_id,
            messages=messages,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )

        # TODO: Persist conversation and message to PostgreSQL

        return {
            "conversation_id": body.conversation_id or "new",
            "content": response.content,
            "model": response.model,
            "provider": response.provider,
            "finish_reason": response.finish_reason,
            "usage": {
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest):
    """Send a chat message and receive a streaming SSE response."""
    llm_factory: LLMFactory = request.app.state.llm_factory

    messages = []
    if body.system_prompt:
        messages.append({"role": "system", "content": body.system_prompt})
    messages.append({"role": "user", "content": body.message})

    async def event_generator():
        try:
            async for chunk in llm_factory.stream(
                provider=body.model_provider,
                model=body.model_id,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
