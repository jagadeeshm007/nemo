# ==============================================================================
# Workflow Service — Workflow Engine (Domain Core)
# ==============================================================================
#
# Responsible for:
#   - Loading workflow definitions from YAML configs
#   - Resolving step dependency graphs (topological ordering)
#   - Executing multi-step workflows with parallel & sequential stages
#   - Managing workflow run state machines
#   - Publishing lifecycle events to Kafka
# ==============================================================================

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────


class StepType(StrEnum):
    LLM_CALL = "llm_call"
    LLM_REASONING = "llm_reasoning"
    TOOL_CALL = "tool_call"
    TOOL_EXECUTION = "tool_execution"
    RAG_QUERY = "rag_query"
    CONDITION = "condition"
    CONDITIONAL = "conditional"
    HUMAN_APPROVAL = "human_approval"
    TRANSFORM = "transform"
    PARALLEL_GROUP = "parallel_group"
    RESPONSE_GENERATION = "response_generation"
    AGENT_LOOP = "agent_loop"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # waiting for human approval


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class StepDefinition:
    """A single step within a workflow definition."""

    id: str
    name: str
    type: StepType
    config: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 120
    retry_count: int = 0
    condition: str | None = None


@dataclass
class WorkflowDefinition:
    """A complete workflow definition loaded from YAML."""

    id: str
    name: str
    description: str
    version: str
    steps: list[StepDefinition] = field(default_factory=list)
    input_schema: dict = field(default_factory=dict)
    output_mapping: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    max_retries: int = 2
    timeout_seconds: int = 600


@dataclass
class StepResult:
    """Result of executing a single step."""

    step_id: str
    status: RunStatus
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0


@dataclass
class WorkflowRun:
    """Runtime state of a single workflow execution."""

    run_id: str
    workflow_id: str
    status: RunStatus = RunStatus.PENDING
    input_data: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    step_results: dict[str, StepResult] = field(default_factory=dict)
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: str = ""


# ── Workflow Engine ──────────────────────────────────────────────────────────


class WorkflowEngine:
    """
    Core engine that manages workflow lifecycle:
      1. Load definitions from YAML
      2. Validate DAGs (no cycles)
      3. Execute steps respecting dependency ordering
      4. Track run state and publish events
    """

    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._runs: dict[str, WorkflowRun] = {}  # in-memory; production: DB
        self._global_timeout: int = 600
        self._max_concurrent: int = 20
        self._background_tasks: set[asyncio.Task] = set()

    # ── Config loading ───────────────────────────────────────────────────

    def load_definitions(self, config_path: str) -> None:
        """Load workflow definitions from a YAML config file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning("Workflow config not found at %s — skipping", config_path)
            return

        with open(path) as f:
            raw = yaml.safe_load(f)

        if not raw:
            return

        global_cfg = raw.get("global", {})
        self._global_timeout = global_cfg.get("default_timeout", 600)
        self._max_concurrent = global_cfg.get("max_concurrent_workflows", 20)

        for wf_raw in raw.get("workflows", []):
            steps = []
            for s in wf_raw.get("steps", []):
                steps.append(
                    StepDefinition(
                        id=s["id"],
                        name=s.get("name", s["id"]),
                        type=StepType(s["type"]),
                        config=s.get("config", {}),
                        depends_on=s.get("depends_on", []),
                        timeout_seconds=s.get("timeout", self._global_timeout),
                        retry_count=s.get("retry_count", 0),
                        condition=s.get("condition"),
                    )
                )

            definition = WorkflowDefinition(
                id=wf_raw["id"],
                name=wf_raw["name"],
                description=wf_raw.get("description", ""),
                version=wf_raw.get("version", "1.0.0"),
                steps=steps,
                input_schema=wf_raw.get("input_schema", {}),
                output_mapping=wf_raw.get("output_mapping", {}),
                tags=wf_raw.get("tags", []),
                max_retries=wf_raw.get("max_retries", 2),
                timeout_seconds=wf_raw.get("timeout", self._global_timeout),
            )

            self._validate_dag(definition)
            self._definitions[definition.id] = definition
            logger.info("Loaded workflow definition: %s (%s)", definition.name, definition.id)

        logger.info("Loaded %d workflow definitions", len(self._definitions))

    def _validate_dag(self, wf: WorkflowDefinition) -> None:
        """Validate that the step dependency graph is a valid DAG."""
        g = nx.DiGraph()
        step_ids = {s.id for s in wf.steps}

        for step in wf.steps:
            g.add_node(step.id)
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(
                        f"Workflow '{wf.id}': step '{step.id}' depends on unknown step '{dep}'"
                    )
                g.add_edge(dep, step.id)

        if not nx.is_directed_acyclic_graph(g):
            raise ValueError(f"Workflow '{wf.id}' contains a dependency cycle")

    def _execution_order(self, wf: WorkflowDefinition) -> list[list[str]]:
        """
        Return execution stages — each stage is a list of step IDs
        that can be executed in parallel.
        """
        g = nx.DiGraph()
        for step in wf.steps:
            g.add_node(step.id)
            for dep in step.depends_on:
                g.add_edge(dep, step.id)

        stages: list[list[str]] = []
        for generation in nx.topological_generations(g):
            stages.append(sorted(generation))

        return stages

    # ── Workflow listing / retrieval ─────────────────────────────────────

    def list_definitions(self) -> list[dict]:
        """List all loaded workflow definitions."""
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "version": d.version,
                "step_count": len(d.steps),
                "tags": d.tags,
            }
            for d in self._definitions.values()
        ]

    def get_definition(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._definitions.get(workflow_id)

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    def list_runs(
        self,
        workflow_id: str | None = None,
        status: RunStatus | None = None,
        limit: int = 50,
    ) -> list[dict]:
        runs = self._runs.values()
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        if status:
            runs = [r for r in runs if r.status == status]

        result = []
        for r in sorted(runs, key=lambda x: x.started_at or datetime.min, reverse=True)[:limit]:
            result.append(
                {
                    "run_id": r.run_id,
                    "workflow_id": r.workflow_id,
                    "status": r.status.value,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
            )
        return result

    # ── Workflow Execution ───────────────────────────────────────────────

    async def start_workflow(
        self,
        workflow_id: str,
        input_data: dict,
        user_id: str = "",
    ) -> WorkflowRun:
        """Start a new workflow execution."""
        definition = self._definitions.get(workflow_id)
        if not definition:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        active = sum(1 for r in self._runs.values() if r.status == RunStatus.RUNNING)
        if active >= self._max_concurrent:
            raise RuntimeError("Max concurrent workflows exceeded")

        run = WorkflowRun(
            run_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=RunStatus.PENDING,
            input_data=input_data,
            context={"input": input_data},
            created_by=user_id,
        )
        self._runs[run.run_id] = run

        logger.info(
            "Starting workflow run %s for %s (user=%s)",
            run.run_id,
            workflow_id,
            user_id,
        )

        # Launch execution in background
        task = asyncio.create_task(self._execute_workflow(run, definition))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return run

    async def cancel_workflow(self, run_id: str) -> WorkflowRun | None:
        """Cancel a running workflow."""
        run = self._runs.get(run_id)
        if not run:
            return None
        if run.status == RunStatus.RUNNING:
            run.status = RunStatus.CANCELLED
            run.completed_at = datetime.now(UTC)
            logger.info("Cancelled workflow run %s", run_id)
        return run

    async def _execute_workflow(self, run: WorkflowRun, definition: WorkflowDefinition) -> None:
        """Execute all steps of a workflow respecting dependency order."""
        run.status = RunStatus.RUNNING
        run.started_at = datetime.now(UTC)

        try:
            stages = self._execution_order(definition)
            step_map = {s.id: s for s in definition.steps}

            for stage in stages:
                if run.status == RunStatus.CANCELLED:
                    break

                # Execute all steps in this stage concurrently
                tasks = []
                for step_id in stage:
                    step_def = step_map[step_id]

                    # Evaluate condition if present
                    if step_def.condition and not self._evaluate_condition(
                        step_def.condition, run.context
                    ):
                        run.step_results[step_id] = StepResult(
                            step_id=step_id,
                            status=RunStatus.COMPLETED,
                            output={"skipped": True, "reason": "condition_not_met"},
                            started_at=datetime.now(UTC),
                            completed_at=datetime.now(UTC),
                        )
                        continue

                    tasks.append(self._execute_step(run, step_def))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Check for failures
                for step_id in stage:
                    result = run.step_results.get(step_id)
                    if result and result.status == RunStatus.FAILED:
                        raise RuntimeError(f"Step '{step_id}' failed: {result.error}")

            # Apply output mapping
            if definition.output_mapping:
                run.output = self._apply_output_mapping(definition.output_mapping, run.context)
            else:
                run.output = run.context

            run.status = RunStatus.COMPLETED

        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = str(exc)
            logger.error("Workflow run %s failed: %s", run.run_id, exc)

        finally:
            run.completed_at = datetime.now(UTC)
            logger.info(
                "Workflow run %s finished with status %s",
                run.run_id,
                run.status.value,
            )

    async def _execute_step(self, run: WorkflowRun, step_def: StepDefinition) -> None:
        """Execute a single workflow step."""
        result = StepResult(
            step_id=step_def.id,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        run.step_results[step_def.id] = result

        try:
            output = await asyncio.wait_for(
                self._dispatch_step(step_def, run.context),
                timeout=step_def.timeout_seconds,
            )

            result.status = RunStatus.COMPLETED
            result.output = output

            # Merge step output into run context
            run.context[step_def.id] = output

        except TimeoutError:
            result.status = RunStatus.FAILED
            result.error = f"Step timed out after {step_def.timeout_seconds}s"

        except Exception as exc:
            result.status = RunStatus.FAILED
            result.error = str(exc)

        finally:
            result.completed_at = datetime.now(UTC)
            if result.started_at:
                delta = result.completed_at - result.started_at
                result.duration_ms = delta.total_seconds() * 1000

    async def _dispatch_step(self, step_def: StepDefinition, context: dict) -> Any:
        """Dispatch step execution based on step type."""
        match step_def.type:
            case StepType.LLM_CALL:
                return await self._step_llm_call(step_def, context)
            case StepType.TOOL_CALL:
                return await self._step_tool_call(step_def, context)
            case StepType.RAG_QUERY:
                return await self._step_rag_query(step_def, context)
            case StepType.CONDITION:
                return await self._step_condition(step_def, context)
            case StepType.TRANSFORM:
                return await self._step_transform(step_def, context)
            case StepType.HUMAN_APPROVAL:
                return await self._step_human_approval(step_def, context)
            case _:
                raise ValueError(f"Unknown step type: {step_def.type}")

    # ── Step Implementations ─────────────────────────────────────────────

    async def _step_llm_call(self, step: StepDefinition, ctx: dict) -> dict:
        """Execute an LLM call step via the AI Service."""
        import httpx

        from app.config import settings

        config = step.config
        prompt = config.get("prompt_template", "{input}")

        # Resolve template variables from context
        try:
            resolved_prompt = prompt.format(**ctx.get("input", {}), **ctx)
        except KeyError:
            resolved_prompt = prompt

        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/chat",
                json={
                    "model": config.get("model", "gpt-4o"),
                    "messages": [{"role": "user", "content": resolved_prompt}],
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens", 2048),
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def _step_tool_call(self, step: StepDefinition, ctx: dict) -> dict:
        """Execute a tool/plugin call via the Plugin Service."""
        import httpx

        from app.config import settings

        config = step.config
        plugin_id = config.get("plugin_id", "")
        action = config.get("action", "")
        params = config.get("parameters", {})

        # Resolve dynamic parameters from context
        resolved_params = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("$ctx."):
                path = v[5:].split(".")
                val = ctx
                for p in path:
                    val = val.get(p, {}) if isinstance(val, dict) else {}
                resolved_params[k] = val
            else:
                resolved_params[k] = v

        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            resp = await client.post(
                f"{settings.PLUGIN_SERVICE_URL}/api/v1/plugins/{plugin_id}/execute",
                json={"action_name": action, "parameters": resolved_params},
            )
            resp.raise_for_status()
            return resp.json()

    async def _step_rag_query(self, step: StepDefinition, ctx: dict) -> dict:
        """Execute a RAG query via the Vector Service."""
        import httpx

        from app.config import settings

        config = step.config
        query = config.get("query_template", "{query}")

        try:
            resolved = query.format(**ctx.get("input", {}), **ctx)
        except KeyError:
            resolved = query

        async with httpx.AsyncClient(timeout=step.timeout_seconds) as client:
            resp = await client.post(
                f"{settings.VECTOR_SERVICE_URL}/api/v1/search",
                json={
                    "query": resolved,
                    "collection": config.get("collection", "default"),
                    "top_k": config.get("top_k", 5),
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def _step_condition(self, step: StepDefinition, ctx: dict) -> dict:
        """Evaluate a condition and return the branch."""
        expression = step.config.get("expression", "true")
        result = self._evaluate_condition(expression, ctx)
        return {"result": result, "branch": "true" if result else "false"}

    async def _step_transform(self, step: StepDefinition, ctx: dict) -> dict:
        """Apply data transformation."""
        mapping = step.config.get("mapping", {})
        output = {}
        for key, source in mapping.items():
            if isinstance(source, str) and source.startswith("$ctx."):
                path = source[5:].split(".")
                val = ctx
                for p in path:
                    val = val.get(p, {}) if isinstance(val, dict) else {}
                output[key] = val
            else:
                output[key] = source
        return output

    async def _step_human_approval(self, step: StepDefinition, ctx: dict) -> dict:
        """Placeholder for human-in-the-loop approval."""
        # In production, this would pause and wait for external approval
        logger.info("Human approval step '%s' — auto-approving in dev mode", step.id)
        return {"approved": True, "approver": "auto"}

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _evaluate_condition(expression: str, context: dict) -> bool:
        """Safely evaluate a simple condition expression."""
        # Basic evaluator — production should use a safe expression language
        try:
            return bool(eval(expression, {"__builtins__": {}}, context))
        except Exception:
            return True

    @staticmethod
    def _apply_output_mapping(mapping: dict, context: dict) -> dict:
        output = {}
        for key, source in mapping.items():
            if isinstance(source, str) and source.startswith("$ctx."):
                path = source[5:].split(".")
                val = context
                for p in path:
                    val = val.get(p, {}) if isinstance(val, dict) else {}
                output[key] = val
            elif isinstance(source, str):
                parts = source.split(".")
                val = context
                for p in parts:
                    val = val.get(p, {}) if isinstance(val, dict) else {}
                output[key] = val
            else:
                output[key] = source
        return output


# ── Singleton ────────────────────────────────────────────────────────────────
workflow_engine = WorkflowEngine()
