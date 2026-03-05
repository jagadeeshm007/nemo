# ==============================================================================
# Plugin Service — Plugin Manager (Core Domain Logic)
# ==============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class PluginState(StrEnum):
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class PluginMetadata:
    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    category: str = ""
    icon: str = ""
    permissions: list[str] = field(default_factory=list)


@dataclass
class PluginAction:
    name: str
    description: str
    parameters_schema: dict = field(default_factory=dict)


@dataclass
class PluginInstance:
    metadata: PluginMetadata
    state: PluginState = PluginState.REGISTERED
    config: dict = field(default_factory=dict)
    actions: list[PluginAction] = field(default_factory=list)
    handler: Any = None  # The actual plugin implementation


class PluginInterface:
    """Base class that all plugin implementations must extend."""

    def metadata(self) -> PluginMetadata:
        raise NotImplementedError

    def configure(self, config: dict) -> None:
        raise NotImplementedError

    async def execute(self, action: str, params: dict) -> dict:
        raise NotImplementedError

    async def health(self) -> bool:
        return True


class PluginManager:
    """
    Manages the lifecycle of plugins: registration, activation, deactivation, execution.

    Plugins are loaded from YAML configuration and can be managed via the API/UI.
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        self._plugins: dict[str, PluginInstance] = {}
        if config_path:
            self._load_from_config(Path(config_path))

    def _load_from_config(self, path: Path) -> None:
        """Load plugin definitions from plugins.yaml."""
        if not path.exists():
            logger.warning(f"Plugin config not found: {path}")
            return

        with open(path) as f:
            raw = yaml.safe_load(f)

        for plugin_data in raw.get("plugins", []):
            metadata = PluginMetadata(
                id=plugin_data["id"],
                name=plugin_data["name"],
                version=plugin_data.get("version", "0.0.0"),
                description=plugin_data.get("description", ""),
                author=plugin_data.get("author", ""),
                category=plugin_data.get("category", ""),
                icon=plugin_data.get("icon", ""),
                permissions=plugin_data.get("permissions", []),
            )

            actions = []
            for action_data in plugin_data.get("actions", []):
                actions.append(
                    PluginAction(
                        name=action_data["name"],
                        description=action_data.get("description", ""),
                        parameters_schema=action_data.get("parameters", {}),
                    )
                )

            state = (
                PluginState.ACTIVE if plugin_data.get("enabled", False) else PluginState.INACTIVE
            )

            self._plugins[metadata.id] = PluginInstance(
                metadata=metadata,
                state=state,
                config=plugin_data.get("config_schema", {}),
                actions=actions,
            )

        logger.info(f"Loaded {len(self._plugins)} plugins from config")

    def register(
        self, metadata: PluginMetadata, handler: PluginInterface | None = None
    ) -> PluginInstance:
        """Register a new plugin."""
        instance = PluginInstance(
            metadata=metadata,
            state=PluginState.REGISTERED,
            handler=handler,
        )
        self._plugins[metadata.id] = instance
        logger.info(f"Plugin registered: {metadata.id}")
        return instance

    def activate(self, plugin_id: str) -> PluginInstance:
        """Activate a registered plugin."""
        plugin = self._get_plugin(plugin_id)
        plugin.state = PluginState.ACTIVE
        logger.info(f"Plugin activated: {plugin_id}")
        return plugin

    def deactivate(self, plugin_id: str) -> PluginInstance:
        """Deactivate a plugin."""
        plugin = self._get_plugin(plugin_id)
        plugin.state = PluginState.INACTIVE
        logger.info(f"Plugin deactivated: {plugin_id}")
        return plugin

    def get(self, plugin_id: str) -> PluginInstance | None:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def list_plugins(
        self,
        category: str | None = None,
        active_only: bool = False,
    ) -> list[PluginInstance]:
        """List plugins with optional filters."""
        results = list(self._plugins.values())
        if category:
            results = [p for p in results if p.metadata.category == category]
        if active_only:
            results = [p for p in results if p.state == PluginState.ACTIVE]
        return results

    async def execute_action(
        self,
        plugin_id: str,
        action_name: str,
        params: dict,
    ) -> dict:
        """Execute a plugin action."""
        plugin = self._get_plugin(plugin_id)

        if plugin.state != PluginState.ACTIVE:
            raise ValueError(f"Plugin '{plugin_id}' is not active (state: {plugin.state})")

        if plugin.handler is None:
            raise ValueError(f"Plugin '{plugin_id}' has no handler implementation")

        return await plugin.handler.execute(action_name, params)

    def update_config(self, plugin_id: str, config: dict) -> PluginInstance:
        """Update plugin configuration."""
        plugin = self._get_plugin(plugin_id)
        plugin.config.update(config)
        if plugin.handler:
            plugin.handler.configure(config)
        logger.info(f"Plugin config updated: {plugin_id}")
        return plugin

    def _get_plugin(self, plugin_id: str) -> PluginInstance:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin not found: {plugin_id}")
        return plugin
