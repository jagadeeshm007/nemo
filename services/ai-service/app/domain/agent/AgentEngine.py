# ==============================================================================
# AI Service — Agent Engine (ReAct Pattern)
# ==============================================================================

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.agent.ToolRegistry import ToolRegistry
from app.domain.llm.LLMFactory import LLMFactory
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentStep:
    """Represents a single step in the agent reasoning loop."""

    step_number: int
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    """Final result of an agent execution."""

    conversation_id: str
    response: str
    steps: list[AgentStep]
    total_tokens: int = 0
    execution_time_ms: int = 0
    status: str = "completed"  # completed, failed, max_iterations


REACT_SYSTEM_PROMPT = """You are Nemo, an intelligent AI assistant with access to tools.

When you need to use a tool, respond with this exact format:
Thought: [your reasoning about what to do]
Action: [tool_name]
Action Input: [JSON input for the tool]

When you have enough information to answer, respond with:
Thought: I now have enough information to answer.
Final Answer: [your complete response]

Available tools:
{tool_descriptions}

Always think step-by-step. Use tools when you need external information or actions.
"""


class AgentEngine:
    """
    ReAct-pattern agent engine for multi-step tool execution.

    Orchestrates the reasoning loop:
    1. LLM reasons about the query
    2. LLM selects a tool (or decides to answer)
    3. Tool executes
    4. Result feeds back into context
    5. Repeat until answer or max iterations
    """

    def __init__(
        self,
        llm_factory: LLMFactory,
        tool_registry: ToolRegistry,
    ) -> None:
        self._llm_factory = llm_factory
        self._tool_registry = tool_registry

    async def execute(
        self,
        query: str,
        conversation_id: str | None = None,
        provider: str = "openai",
        model: str = "gpt-4o",
        max_iterations: int = 10,
        system_prompt: str | None = None,
        history: list[dict] | None = None,
        temperature: float = 0.3,
    ) -> AgentResult:
        """Execute the agent reasoning loop synchronously."""
        start_time = time.time()
        conversation_id = conversation_id or str(uuid4())
        steps: list[AgentStep] = []
        total_tokens = 0

        # Build system prompt with tool descriptions
        tool_descriptions = self._tool_registry.get_tool_descriptions()
        full_system_prompt = (system_prompt or REACT_SYSTEM_PROMPT).format(
            tool_descriptions=tool_descriptions
        )

        messages = [{"role": "system", "content": full_system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        for iteration in range(1, max_iterations + 1):
            logger.info(
                f"Agent iteration {iteration}/{max_iterations}",
                extra={"conversation_id": conversation_id},
            )

            response = await self._llm_factory.complete(
                provider=provider,
                model=model,
                messages=messages,
                temperature=temperature,
            )
            total_tokens += response.total_tokens

            content = response.content
            step = AgentStep(step_number=iteration)

            # Parse the response
            if "Final Answer:" in content:
                # Agent decided to give a final answer
                final_answer = content.split("Final Answer:")[-1].strip()
                thought = ""
                if "Thought:" in content:
                    thought = content.split("Thought:")[1].split("Final Answer:")[0].strip()
                step.thought = thought
                step.observation = final_answer
                steps.append(step)

                execution_time = int((time.time() - start_time) * 1000)
                return AgentResult(
                    conversation_id=conversation_id,
                    response=final_answer,
                    steps=steps,
                    total_tokens=total_tokens,
                    execution_time_ms=execution_time,
                    status="completed",
                )

            elif "Action:" in content:
                # Agent wants to use a tool
                thought = ""
                if "Thought:" in content:
                    thought = content.split("Thought:")[1].split("Action:")[0].strip()

                action = content.split("Action:")[1].split("Action Input:")[0].strip()
                action_input = ""
                if "Action Input:" in content:
                    action_input = content.split("Action Input:")[-1].strip()

                step.thought = thought
                step.action = action
                step.action_input = action_input

                # Execute the tool
                tool_result = await self._tool_registry.execute(
                    tool_name=action,
                    params=action_input,
                )
                step.observation = tool_result.output

                steps.append(step)

                # Feed observation back into the conversation
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Observation: {tool_result.output}",
                    }
                )

            else:
                # LLM responded directly without using the format
                step.thought = content
                steps.append(step)

                execution_time = int((time.time() - start_time) * 1000)
                return AgentResult(
                    conversation_id=conversation_id,
                    response=content,
                    steps=steps,
                    total_tokens=total_tokens,
                    execution_time_ms=execution_time,
                    status="completed",
                )

        # Max iterations reached
        execution_time = int((time.time() - start_time) * 1000)
        return AgentResult(
            conversation_id=conversation_id,
            response="I was unable to complete the task within the allowed number of steps. Here's what I found so far:\n\n"
            + (steps[-1].observation if steps else "No results"),
            steps=steps,
            total_tokens=total_tokens,
            execution_time_ms=execution_time,
            status="max_iterations",
        )

    async def execute_stream(
        self,
        query: str,
        conversation_id: str | None = None,
        provider: str = "openai",
        model: str = "gpt-4o",
        max_iterations: int = 10,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """Execute the agent loop and stream events."""
        # For streaming, we yield step-by-step updates
        result = await self.execute(
            query=query,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            max_iterations=max_iterations,
            **kwargs,
        )

        for step in result.steps:
            yield {
                "event": "step",
                "data": {
                    "step_number": step.step_number,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation,
                },
            }

        yield {
            "event": "done",
            "data": {
                "response": result.response,
                "total_tokens": result.total_tokens,
                "execution_time_ms": result.execution_time_ms,
                "status": result.status,
            },
        }
