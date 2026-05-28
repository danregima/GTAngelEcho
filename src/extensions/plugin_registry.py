"""
Plugin Registry — Discovery, loading, and lifecycle management for plugins.

KSM Cycle 2: Core infrastructure for The Void (Property 13).
"""
import os
import sys
import logging
import importlib
import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("PluginRegistry")


class PluginState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMeta:
    """Metadata describing a plugin."""
    name: str
    version: str = "0.1.0"
    author: str = "unknown"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)      # Hook points this plugin uses
    events: List[str] = field(default_factory=list)      # Events this plugin emits
    config_schema: Dict[str, Any] = field(default_factory=dict)


class PluginBase(ABC):
    """
    Abstract base class for all GTAngelEcho plugins.

    Plugins MUST implement:
    - meta(): Return PluginMeta describing the plugin
    - on_enable(context): Called when plugin is enabled
    - on_disable(): Called when plugin is disabled

    Plugins MAY implement:
    - on_tick(tick_result): Called each game tick with the tick result
    - on_event(event): Called for subscribed events
    - configure(config): Called with plugin-specific configuration
    """

    @abstractmethod
    def meta(self) -> PluginMeta:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def on_enable(self, context: Dict[str, Any]):
        """
        Called when the plugin is enabled.

        Args:
            context: Dict containing references to core systems:
                - "event_bus": The EventBus instance
                - "hooks": The HookSystem instance
                - "endocrine": The VirtualEndocrineSystem
                - "memory": The CognitiveMemorySystem
                - "config": Plugin-specific configuration dict
        """
        ...

    @abstractmethod
    def on_disable(self):
        """Called when the plugin is disabled. Clean up resources."""
        ...

    def on_tick(self, tick_result: Dict[str, Any]):
        """Called each game tick. Override to react to tick data."""
        pass

    def on_event(self, event):
        """Called for subscribed events. Override to handle events."""
        pass

    def configure(self, config: Dict[str, Any]):
        """Called with plugin-specific configuration."""
        pass


@dataclass
class _PluginEntry:
    """Internal registry entry for a plugin."""
    plugin: PluginBase
    meta: PluginMeta
    state: PluginState = PluginState.DISCOVERED
    error: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


class PluginRegistry:
    """
    Plugin Registry — Discovers, loads, enables, and manages plugins.

    Features:
    - File-based plugin discovery from a directory
    - Class-based plugin registration (for built-in plugins)
    - Dependency resolution
    - Lifecycle management (enable/disable)
    - Per-tick dispatch to enabled plugins
    - Plugin configuration
    """

    def __init__(self):
        self._plugins: Dict[str, _PluginEntry] = {}
        self._load_order: List[str] = []
        logger.info("PluginRegistry initialized")

    # ── Registration ───────────────────────────────────────────

    def register(self, plugin: PluginBase, config: Optional[Dict] = None) -> bool:
        """
        Register a plugin instance.

        Args:
            plugin: An instance of PluginBase.
            config: Optional configuration dict for the plugin.

        Returns:
            True if registered successfully.
        """
        meta = plugin.meta()
        if meta.name in self._plugins:
            logger.warning(f"Plugin '{meta.name}' already registered, skipping")
            return False

        entry = _PluginEntry(
            plugin=plugin,
            meta=meta,
            state=PluginState.LOADED,
            config=config or {}
        )
        self._plugins[meta.name] = entry
        logger.info(f"Registered plugin: {meta.name} v{meta.version}")
        return True

    def discover(self, plugin_dir: str) -> List[str]:
        """
        Discover and load plugins from a directory.

        Each plugin should be a Python file containing a class that
        inherits from PluginBase. The file must define a top-level
        function `create_plugin() -> PluginBase`.

        Args:
            plugin_dir: Absolute path to the plugins directory.

        Returns:
            List of discovered plugin names.
        """
        discovered = []
        if not os.path.isdir(plugin_dir):
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return discovered

        for filename in sorted(os.listdir(plugin_dir)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue

            filepath = os.path.join(plugin_dir, filename)
            module_name = f"plugin_{filename[:-3]}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "create_plugin"):
                    plugin = module.create_plugin()
                    if isinstance(plugin, PluginBase):
                        self.register(plugin)
                        discovered.append(plugin.meta().name)
                    else:
                        logger.warning(f"{filename}: create_plugin() did not return PluginBase")
                else:
                    logger.warning(f"{filename}: No create_plugin() function found")

            except Exception as e:
                logger.error(f"Failed to load plugin from {filename}: {e}")

        logger.info(f"Discovered {len(discovered)} plugins from {plugin_dir}")
        return discovered

    # ── Lifecycle ──────────────────────────────────────────────

    def enable(self, name: str, context: Dict[str, Any]) -> bool:
        """
        Enable a plugin, calling its on_enable() method.

        Args:
            name: Plugin name.
            context: System context dict passed to the plugin.

        Returns:
            True if enabled successfully.
        """
        entry = self._plugins.get(name)
        if not entry:
            logger.error(f"Plugin '{name}' not found")
            return False

        if entry.state == PluginState.ENABLED:
            logger.warning(f"Plugin '{name}' already enabled")
            return True

        # Check dependencies
        for dep in entry.meta.dependencies:
            dep_entry = self._plugins.get(dep)
            if not dep_entry or dep_entry.state != PluginState.ENABLED:
                logger.error(f"Plugin '{name}' requires '{dep}' to be enabled first")
                return False

        try:
            # Merge config into context
            ctx = {**context, "config": entry.config}
            entry.plugin.configure(entry.config)
            entry.plugin.on_enable(ctx)
            entry.state = PluginState.ENABLED
            self._load_order.append(name)
            logger.info(f"Enabled plugin: {name}")
            return True
        except Exception as e:
            entry.state = PluginState.ERROR
            entry.error = str(e)
            logger.error(f"Failed to enable plugin '{name}': {e}")
            return False

    def disable(self, name: str) -> bool:
        """Disable a plugin, calling its on_disable() method."""
        entry = self._plugins.get(name)
        if not entry:
            return False

        if entry.state != PluginState.ENABLED:
            return True

        try:
            entry.plugin.on_disable()
            entry.state = PluginState.DISABLED
            if name in self._load_order:
                self._load_order.remove(name)
            logger.info(f"Disabled plugin: {name}")
            return True
        except Exception as e:
            entry.state = PluginState.ERROR
            entry.error = str(e)
            logger.error(f"Error disabling plugin '{name}': {e}")
            return False

    def enable_all(self, context: Dict[str, Any]):
        """Enable all registered plugins in dependency order."""
        # Simple topological sort: enable plugins with no unmet dependencies first
        enabled = set()
        remaining = set(self._plugins.keys())

        max_iterations = len(remaining) + 1
        for _ in range(max_iterations):
            if not remaining:
                break
            for name in list(remaining):
                entry = self._plugins[name]
                deps_met = all(d in enabled for d in entry.meta.dependencies)
                if deps_met:
                    if self.enable(name, context):
                        enabled.add(name)
                    remaining.discard(name)

        if remaining:
            logger.warning(f"Could not enable plugins (unmet deps): {remaining}")

    def disable_all(self):
        """Disable all plugins in reverse load order."""
        for name in reversed(self._load_order[:]):
            self.disable(name)

    # ── Dispatch ───────────────────────────────────────────────

    def dispatch_tick(self, tick_result: Dict[str, Any]):
        """Dispatch tick data to all enabled plugins."""
        for name in self._load_order:
            entry = self._plugins.get(name)
            if entry and entry.state == PluginState.ENABLED:
                try:
                    entry.plugin.on_tick(tick_result)
                except Exception as e:
                    logger.error(f"Plugin '{name}' tick error: {e}")

    def dispatch_event(self, event):
        """Dispatch an event to all enabled plugins."""
        for name in self._load_order:
            entry = self._plugins.get(name)
            if entry and entry.state == PluginState.ENABLED:
                # Only dispatch if plugin subscribes to this event type
                if "*" in entry.meta.events or event.type in entry.meta.events:
                    try:
                        entry.plugin.on_event(event)
                    except Exception as e:
                        logger.error(f"Plugin '{name}' event error: {e}")

    # ── Query ──────────────────────────────────────────────────

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins with their state."""
        return [
            {
                "name": entry.meta.name,
                "version": entry.meta.version,
                "state": entry.state.value,
                "author": entry.meta.author,
                "description": entry.meta.description,
                "error": entry.error,
            }
            for entry in self._plugins.values()
        ]

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin instance by name."""
        entry = self._plugins.get(name)
        return entry.plugin if entry else None

    def is_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        entry = self._plugins.get(name)
        return entry is not None and entry.state == PluginState.ENABLED

    @property
    def enabled_count(self) -> int:
        """Number of currently enabled plugins."""
        return sum(1 for e in self._plugins.values() if e.state == PluginState.ENABLED)

    @property
    def total_count(self) -> int:
        """Total number of registered plugins."""
        return len(self._plugins)
