# ==============================================================================
# Workflow Service — Workflow Routes
# ==============================================================================

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────


class StartWorkflowRequest(BaseModel):
    workflow_id: str
    input_data: dict = {}
    user_id: str = ""


class UpsertWorkflowRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: list[dict] = []
    input_schema: dict = {}
    output_mapping: dict = {}
    tags: list[str] = []


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/workflows")
async def list_workflows(request: Request):
    """List all workflow definitions."""
    engine = request.app.state.workflow_engine
    return {"workflows": engine.list_definitions()}


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, request: Request):
    """Get workflow definition details."""
    engine = request.app.state.workflow_engine
    definition = engine.get_definition(workflow_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": definition.id,
        "name": definition.name,
        "description": definition.description,
        "version": definition.version,
        "steps": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "depends_on": s.depends_on,
                "timeout": s.timeout_seconds,
                "condition": s.condition,
            }
            for s in definition.steps
        ],
        "input_schema": definition.input_schema,
        "output_mapping": definition.output_mapping,
        "tags": definition.tags,
    }


@router.post("/workflows/start")
async def start_workflow(body: StartWorkflowRequest, request: Request):
    """Start a new workflow execution."""
    engine = request.app.state.workflow_engine
    try:
        run = await engine.start_workflow(
            workflow_id=body.workflow_id,
            input_data=body.input_data,
            user_id=body.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return {
        "run_id": run.run_id,
        "workflow_id": run.workflow_id,
        "status": run.status.value,
    }


@router.get("/workflows/runs")
async def list_runs(
    request: Request,
    workflow_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    """List workflow runs with optional filtering."""
    engine = request.app.state.workflow_engine
    from app.domain.WorkflowEngine import RunStatus

    run_status = None
    if status:
        try:
            run_status = RunStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from None

    runs = engine.list_runs(workflow_id=workflow_id, status=run_status, limit=limit)
    return {"runs": runs, "total": len(runs)}


@router.get("/workflows/runs/{run_id}")
async def get_run(run_id: str, request: Request):
    """Get details of a specific workflow run."""
    engine = request.app.state.workflow_engine
    run = engine.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": run.run_id,
        "workflow_id": run.workflow_id,
        "status": run.status.value,
        "input_data": run.input_data,
        "output": run.output,
        "error": run.error,
        "step_results": {
            sid: {
                "status": sr.status.value,
                "output": sr.output,
                "error": sr.error,
                "duration_ms": sr.duration_ms,
            }
            for sid, sr in run.step_results.items()
        },
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.post("/workflows/runs/{run_id}/cancel")
async def cancel_run(run_id: str, request: Request):
    """Cancel a running workflow."""
    engine = request.app.state.workflow_engine
    run = await engine.cancel_workflow(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {"run_id": run.run_id, "status": run.status.value}
