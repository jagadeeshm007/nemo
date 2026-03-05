# ==============================================================================
# Plugin Service — Plugin Routes
# ==============================================================================

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ExecuteActionRequest(BaseModel):
    action_name: str
    parameters: dict = {}


class UpdateConfigRequest(BaseModel):
    config: dict


@router.get("/plugins")
async def list_plugins(category: str | None = None, active_only: bool = False):
    """List all registered plugins."""
    # TODO: Use PluginManager from app.state
    return {"plugins": [], "total": 0}


@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details."""
    return {"id": plugin_id, "status": "pending_implementation"}


@router.post("/plugins/{plugin_id}/activate")
async def activate_plugin(plugin_id: str):
    """Activate a plugin."""
    return {"id": plugin_id, "state": "active"}


@router.post("/plugins/{plugin_id}/deactivate")
async def deactivate_plugin(plugin_id: str):
    """Deactivate a plugin."""
    return {"id": plugin_id, "state": "inactive"}


@router.put("/plugins/{plugin_id}/config")
async def update_plugin_config(plugin_id: str, body: UpdateConfigRequest):
    """Update plugin configuration."""
    return {"id": plugin_id, "config_updated": True}


@router.post("/plugins/{plugin_id}/execute")
async def execute_action(plugin_id: str, body: ExecuteActionRequest):
    """Execute a plugin action."""
    return {
        "plugin_id": plugin_id,
        "action": body.action_name,
        "status": "pending_implementation",
    }
