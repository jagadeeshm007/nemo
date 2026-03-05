# ==============================================================================
# AI Service — LLM Factory (Dynamic Provider Instantiation)
# ==============================================================================

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

import yaml

from app.domain.llm.LLMProvider import LLMProvider, LLMProviderConfig, ModelConfig
from app.domain.llm.providers.OpenAIProvider import OpenAIProvider
from app.domain.llm.providers.AnthropicProvider import AnthropicProvider
from app.domain.llm.providers.GeminiProvider import GeminiProvider
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Registry of provider implementations
_PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GeminiProvider,
}


class LLMFactory:
    """
    Factory for creating LLM provider instances.

    Loads provider configuration from YAML and instantiates providers
    dynamically. New providers can be registered without modifying core logic.
    """

    def __init__(self, config_path: Path | str) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._configs: dict[str, LLMProviderConfig] = {}
        self._config_path = Path(config_path)
        self._load_config()

    def _load_config(self) -> None:
        """Load provider configuration from YAML file."""
        if not self._config_path.exists():
            logger.warning(
                "Models config not found, using defaults",
                extra={"path": str(self._config_path)},
            )
            return

        with open(self._config_path) as f:
            raw = yaml.safe_load(f)

        for provider_data in raw.get("providers", []):
            name = provider_data["name"]
            api_key_env = provider_data.get("api_key_env", "")
            api_key = os.environ.get(api_key_env, "")

            models = []
            for m in provider_data.get("models", []):
                models.append(
                    ModelConfig(
                        id=m["id"],
                        display_name=m.get("display_name", m["id"]),
                        enabled=m.get("enabled", True),
                        max_tokens=m.get("max_tokens", 4096),
                        supports_streaming=m.get("supports_streaming", False),
                        supports_tools=m.get("supports_tools", False),
                        supports_vision=m.get("supports_vision", False),
                        cost_per_1k_input=m.get("cost_per_1k_input", 0.0),
                        cost_per_1k_output=m.get("cost_per_1k_output", 0.0),
                    )
                )

            config = LLMProviderConfig(
                name=name,
                display_name=provider_data.get("display_name", name),
                enabled=provider_data.get("enabled", False),
                api_key=api_key,
                base_url=provider_data.get("base_url", ""),
                timeout_seconds=provider_data.get("timeout_seconds", 120),
                max_retries=provider_data.get("max_retries", 3),
                models=models,
            )
            self._configs[name] = config

            if config.enabled and api_key:
                self._instantiate_provider(name, config)

        logger.info(
            "LLM Factory loaded",
            extra={
                "total_providers": len(self._configs),
                "active_providers": len(self._providers),
            },
        )

    def _instantiate_provider(self, name: str, config: LLMProviderConfig) -> None:
        """Instantiate a provider from the registry."""
        provider_cls = _PROVIDER_REGISTRY.get(name)
        if provider_cls is None:
            logger.warning(f"No implementation registered for provider: {name}")
            return

        try:
            self._providers[name] = provider_cls(config)
            logger.info(f"Provider instantiated: {name}")
        except Exception as e:
            logger.error(f"Failed to instantiate provider {name}: {e}")

    # =========================================================================
    # Public API
    # =========================================================================

    @staticmethod
    def register_provider(name: str, provider_cls: type[LLMProvider]) -> None:
        """Register a new provider implementation (plugin-style extensibility)."""
        _PROVIDER_REGISTRY[name] = provider_cls
        logger.info(f"Provider registered: {name}")

    def get_provider(self, name: str) -> LLMProvider:
        """Get an active provider by name."""
        provider = self._providers.get(name)
        if provider is None:
            raise ValueError(
                f"Provider '{name}' is not available. "
                f"Active providers: {list(self._providers.keys())}"
            )
        return provider

    def list_providers(self) -> list[str]:
        """Return names of all active providers."""
        return list(self._providers.keys())

    def list_all_configs(self) -> list[LLMProviderConfig]:
        """Return configuration for all providers (including disabled)."""
        return list(self._configs.values())

    def get_config(self, provider_name: str) -> LLMProviderConfig | None:
        """Get configuration for a specific provider."""
        return self._configs.get(provider_name)

    def list_models(self, provider_name: str | None = None, enabled_only: bool = True) -> list[dict]:
        """List all available models, optionally filtered by provider."""
        results = []
        for name, config in self._configs.items():
            if provider_name and name != provider_name:
                continue
            if not config.enabled and enabled_only:
                continue
            for model in config.models:
                if enabled_only and not model.enabled:
                    continue
                results.append(
                    {
                        "provider": name,
                        "model_id": model.id,
                        "display_name": model.display_name,
                        "enabled": model.enabled,
                        "max_tokens": model.max_tokens,
                        "supports_streaming": model.supports_streaming,
                        "supports_tools": model.supports_tools,
                        "supports_vision": model.supports_vision,
                    }
                )
        return results

    async def complete(
        self,
        provider: str,
        model: str,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        """Send a completion request to the specified provider/model."""
        p = self.get_provider(provider)
        return await p.complete(model, messages, **kwargs)

    async def stream(
        self,
        provider: str,
        model: str,
        messages: list[dict],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a completion response from the specified provider/model."""
        p = self.get_provider(provider)
        async for chunk in p.stream(model, messages, **kwargs):
            yield chunk

    async def embed(self, provider: str, text: str | list[str]) -> list[list[float]]:
        """Generate embeddings using the specified provider."""
        p = self.get_provider(provider)
        return await p.embed(text)

    def reload_config(self) -> None:
        """Reload configuration from YAML (for runtime updates)."""
        self._providers.clear()
        self._configs.clear()
        self._load_config()
