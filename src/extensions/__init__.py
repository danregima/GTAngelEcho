"""
GTAngelEcho Extension Architecture
Provides Plugin Registry, Event Bus, and Hook System.

KSM Cycle 2: Strengthening The Void (Property 13).
"""
from extensions.plugin_registry import PluginRegistry, PluginBase, PluginMeta
from extensions.event_bus import EventBus, Event, EventPriority
from extensions.hooks import HookSystem, HookPoint

__all__ = [
    "PluginRegistry", "PluginBase", "PluginMeta",
    "EventBus", "Event", "EventPriority",
    "HookSystem", "HookPoint",
]
