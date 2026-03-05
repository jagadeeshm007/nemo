# ==============================================================================
# AI Service — Agent Routes
# ==============================================================================

from __future__ import annotations

import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.domain.agent.AgentEngine import AgentEngine
from app.domain.agent.ToolRegistry import ToolRegistry
from app.domain.llm.LLMFactory import LLMFactory
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AgentExecuteRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    model_provider: str = "openai"
    model_id: str = "gpt-4o"
    max_iterations: int = 10
    system_prompt: str | None = None
    tools: list[str] | None = None


@router.post("/agent/execute")
async def agent_execute(request: Request, body: AgentExecuteRequest):
    """Execute the agent reasoning loop synchronously."""
    llm_factory: LLMFactory = request.app.state.llm_factory
    tool_registry = ToolRegistry()  # TODO: Load from Plugin Service

    engine = AgentEngine(llm_factory, tool_registry)

    try:
        result = await engine.execute(
            query=body.query,
            conversation_id=body.conversation_id,
            provider=body.model_provider,
            model=body.model_id,
            max_iterations=body.max_iterations,
            system_prompt=body.system_prompt,
        )

        # Publish event to Kafka
        kafka = request.app.state.kafka
        await kafka.publish(
            topic="nemo.tools.executed",
            event_type="AgentExecutionCompleted",
            payload={
                "conversation_id": result.conversation_id,
                "status": result.status,
                "steps": len(result.steps),
                "total_tokens": result.total_tokens,
            },
        )

        return {
            "conversation_id": result.conversation_id,
            "response": result.response,
            "steps": [
                {
                    "step_number": s.step_number,
                    "thought": s.thought,
                    "action": s.action,
                    "action_input": s.action_input,
                    "observation": s.observation,
                }
                for s in result.steps
            ],
            "total_tokens": result.total_tokens,
            "execution_time_ms": result.execution_time_ms,
            "status": result.status,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agent/execute/stream")
async def agent_execute_stream(request: Request, body: AgentExecuteRequest):
    """Execute the agent with streaming SSE events."""
    llm_factory: LLMFactory = request.app.state.llm_factory
    tool_registry = ToolRegistry()

    engine = AgentEngine(llm_factory, tool_registry)

    async def event_generator():
        try:
            async for event in engine.execute_stream(
                query=body.query,
                conversation_id=body.conversation_id,
                provider=body.model_provider,
                model=body.model_id,
                max_iterations=body.max_iterations,
                system_prompt=body.system_prompt,
            ):
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
