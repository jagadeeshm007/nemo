# ==============================================================================
# AI Service — Model Routes
# ==============================================================================

from fastapi import APIRouter, Request

from app.domain.llm.LLMFactory import LLMFactory

router = APIRouter()


@router.get("/models")
async def list_models(
    request: Request,
    provider: str | None = None,
    enabled_only: bool = True,
):
    """List available LLM models, optionally filtered by provider."""
    llm_factory: LLMFactory = request.app.state.llm_factory
    models = llm_factory.list_models(provider_name=provider, enabled_only=enabled_only)
    return {"models": models, "total": len(models)}


@router.get("/models/providers")
async def list_providers(request: Request):
    """List active LLM providers."""
    llm_factory: LLMFactory = request.app.state.llm_factory
    return {
        "active_providers": llm_factory.list_providers(),
        "all_configs": [
            {
                "name": c.name,
                "display_name": c.display_name,
                "enabled": c.enabled,
                "model_count": len(c.models),
            }
            for c in llm_factory.list_all_configs()
        ],
    }


@router.post("/models/reload")
async def reload_models(request: Request):
    """Reload model configuration from YAML file."""
    llm_factory: LLMFactory = request.app.state.llm_factory
    llm_factory.reload_config()
    return {
        "status": "reloaded",
        "active_providers": llm_factory.list_providers(),
    }
