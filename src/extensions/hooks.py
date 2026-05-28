"""
Hook System — Named interception points in the GTAngelEcho pipeline.
Allows plugins to modify data flowing between centers.

KSM Cycle 2: Core infrastructure for The Void (Property 13).
"""
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("HookSystem")


class HookPoint(Enum):
    """
    Named hook points in the GTAngelEcho pipeline.
    Plugins can attach to these to intercept and modify data.
    """
    # Tick lifecycle
    PRE_TICK = "pre_tick"                       # Before any tick processing
    POST_TICK = "post_tick"                     # After tick result is compiled

    # Endocrine hooks
    PRE_ENDOCRINE_TICK = "pre_endocrine_tick"   # Before hormone decay
    POST_ENDOCRINE_TICK = "post_endocrine_tick" # After mode detection
    ENDOCRINE_EVENT = "endocrine_event"         # When an event is signaled

    # Cognitive hooks
    PRE_PERCEIVE = "pre_perceive"               # Before perception phase
    POST_PERCEIVE = "post_perceive"             # After perception, before resonance
    PRE_SYNTHESIZE = "pre_synthesize"           # Before action potential generation
    POST_SYNTHESIZE = "post_synthesize"         # After synthesis, before enactment
    POST_ENACT = "post_enact"                   # After action selection

    # Avatar hooks
    PRE_EXPRESSION = "pre_expression"           # Before FACS update
    POST_EXPRESSION = "post_expression"         # After expression state generated
    PRE_EMBODIMENT = "pre_embodiment"           # Before embodiment update
    POST_EMBODIMENT = "post_embodiment"         # After embodiment state generated

    # Navigation hooks
    PRE_NAVIGATION = "pre_navigation"           # Before nav tick
    POST_NAVIGATION = "post_navigation"         # After nav tick
    MISSION_ASSIGNED = "mission_assigned"       # When a new mission starts
    MISSION_COMPLETE = "mission_complete"       # When a mission completes

    # Memory hooks
    PRE_MEMORY_STORE = "pre_memory_store"       # Before storing a memory
    POST_MEMORY_RECALL = "post_memory_recall"   # After memory retrieval


@dataclass
class _HookHandler:
    """Internal handler registration."""
    callback: Callable
    priority: int = 50
    name: str = ""


class HookSystem:
    """
    Hook System — Allows plugins to intercept and modify data at named
    pipeline points.

    Unlike the EventBus (fire-and-forget notifications), hooks allow
    handlers to modify the data flowing through the pipeline.

    Usage:
        hooks = HookSystem()
        hooks.add(HookPoint.POST_TICK, my_modifier, priority=10)
        result = hooks.apply(HookPoint.POST_TICK, tick_data)
    """

    def __init__(self):
        self._hooks: Dict[HookPoint, List[_HookHandler]] = {hp: [] for hp in HookPoint}
        logger.info(f"HookSystem initialized ({len(HookPoint)} hook points)")

    def add(self, hook_point: HookPoint, callback: Callable,
            priority: int = 50, name: str = "") -> None:
        """
        Register a hook handler.

        Args:
            hook_point: The pipeline point to hook into.
            callback: Callable(data: Any) -> Any. Must return the (possibly modified) data.
            priority: Lower values execute first.
            name: Optional name for debugging.
        """
        handler = _HookHandler(callback=callback, priority=priority, name=name)
        self._hooks[hook_point].append(handler)
        self._hooks[hook_point].sort(key=lambda h: h.priority)
        logger.info(f"Hook registered: {hook_point.value} ← {name or 'anonymous'} (priority={priority})")

    def remove(self, hook_point: HookPoint, callback: Callable) -> bool:
        """Remove a specific handler from a hook point."""
        before = len(self._hooks[hook_point])
        self._hooks[hook_point] = [
            h for h in self._hooks[hook_point] if h.callback is not callback
        ]
        return len(self._hooks[hook_point]) < before

    def apply(self, hook_point: HookPoint, data: Any) -> Any:
        """
        Apply all handlers at a hook point to the data.

        Each handler receives the data and must return it (possibly modified).
        Handlers execute in priority order.

        Args:
            hook_point: The pipeline point.
            data: The data to pass through handlers.

        Returns:
            The data after all handlers have processed it.
        """
        for handler in self._hooks[hook_point]:
            try:
                result = handler.callback(data)
                if result is not None:
                    data = result
            except Exception as e:
                logger.error(f"Hook error at {hook_point.value} ({handler.name}): {e}")
        return data

    def has_handlers(self, hook_point: HookPoint) -> bool:
        """Check if a hook point has any registered handlers."""
        return len(self._hooks[hook_point]) > 0

    def handler_count(self, hook_point: Optional[HookPoint] = None) -> int:
        """Get handler count for a specific hook point or all."""
        if hook_point:
            return len(self._hooks[hook_point])
        return sum(len(handlers) for handlers in self._hooks.values())

    def list_hooks(self) -> Dict[str, int]:
        """List all hook points and their handler counts."""
        return {hp.value: len(handlers) for hp, handlers in self._hooks.items()}

    def clear(self, hook_point: Optional[HookPoint] = None):
        """Clear handlers for a specific hook point or all."""
        if hook_point:
            self._hooks[hook_point].clear()
        else:
            for hp in self._hooks:
                self._hooks[hp].clear()


if __name__ == "__main__":
    hooks = HookSystem()

    # Example: modifier that boosts aggression
    def aggression_boost(data):
        if isinstance(data, dict) and "action_potentials" in data:
            data["action_potentials"]["engage"] *= 1.5
            logger.info(f"  [Hook] Boosted engage potential")
        return data

    hooks.add(HookPoint.POST_SYNTHESIZE, aggression_boost, priority=10, name="aggression_boost")

    # Simulate applying the hook
    test_data = {"action_potentials": {"engage": 0.5, "explore": 0.3}}
    result = hooks.apply(HookPoint.POST_SYNTHESIZE, test_data)
    logger.info(f"Result: {result}")
    logger.info(f"Hook points: {hooks.list_hooks()}")
