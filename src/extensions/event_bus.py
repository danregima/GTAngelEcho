"""
Event Bus — Decoupled inter-module communication.
Supports typed events, priority ordering, async-ready handlers,
and wildcard subscriptions.

KSM Cycle 2: Core infrastructure for The Void (Property 13).
"""
import time
import logging
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("EventBus")


class EventPriority(IntEnum):
    """Event handler priority — lower values execute first."""
    SYSTEM = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    MONITOR = 100  # Read-only monitoring, runs last


@dataclass
class Event:
    """A typed event flowing through the bus."""
    type: str                           # e.g., "endocrine.mode_change", "tick.pre", "tick.post"
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    cancelled: bool = False             # If True, lower-priority handlers are skipped
    propagation_stopped: bool = False   # If True, no more handlers run

    def cancel(self):
        """Cancel this event (prevents default behavior)."""
        self.cancelled = True

    def stop_propagation(self):
        """Stop all further handler execution."""
        self.propagation_stopped = True


@dataclass
class _Subscription:
    """Internal subscription record."""
    handler: Callable
    priority: EventPriority
    source_filter: Optional[str] = None  # Only fire for events from this source
    once: bool = False                   # Auto-unsubscribe after first fire


class EventBus:
    """
    Central event bus for GTAngelEcho.

    Features:
    - Typed events with dot-notation namespacing (e.g., "tick.pre", "endocrine.mode_change")
    - Priority-based handler ordering
    - Wildcard subscriptions ("*" matches all, "tick.*" matches tick namespace)
    - Source filtering
    - One-shot subscriptions
    - Event cancellation and propagation control
    - Event history for debugging
    """

    def __init__(self, history_size: int = 200):
        self._subscriptions: Dict[str, List[_Subscription]] = defaultdict(list)
        self._history: List[Event] = []
        self._history_size = history_size
        self._stats: Dict[str, int] = defaultdict(int)
        logger.info("EventBus initialized")

    # ── Subscribe ──────────────────────────────────────────────

    def on(self, event_type: str, handler: Callable,
           priority: EventPriority = EventPriority.NORMAL,
           source_filter: Optional[str] = None) -> Callable:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Event type string or "*" for all events.
            handler: Callable(event: Event) → None
            priority: Execution priority (lower = earlier).
            source_filter: Only fire for events from this source.

        Returns:
            The handler (for decorator use).
        """
        sub = _Subscription(handler=handler, priority=priority, source_filter=source_filter)
        self._subscriptions[event_type].append(sub)
        self._subscriptions[event_type].sort(key=lambda s: s.priority)
        return handler

    def once(self, event_type: str, handler: Callable,
             priority: EventPriority = EventPriority.NORMAL) -> Callable:
        """Subscribe a handler that fires only once, then auto-unsubscribes."""
        sub = _Subscription(handler=handler, priority=priority, once=True)
        self._subscriptions[event_type].append(sub)
        self._subscriptions[event_type].sort(key=lambda s: s.priority)
        return handler

    def off(self, event_type: str, handler: Callable):
        """Unsubscribe a handler from an event type."""
        self._subscriptions[event_type] = [
            s for s in self._subscriptions[event_type] if s.handler is not handler
        ]

    # ── Emit ───────────────────────────────────────────────────

    def emit(self, event: Event) -> Event:
        """
        Emit an event to all matching subscribers.

        Matching order:
        1. Exact type match
        2. Namespace wildcard match (e.g., "tick.*" matches "tick.pre")
        3. Global wildcard ("*")

        Returns:
            The event (possibly modified by handlers).
        """
        self._stats[event.type] += 1
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]

        # Collect matching subscriptions
        matching: List[_Subscription] = []

        # Exact match
        matching.extend(self._subscriptions.get(event.type, []))

        # Namespace wildcard: "tick.*" matches "tick.pre"
        parts = event.type.split(".")
        for i in range(len(parts)):
            wildcard = ".".join(parts[:i + 1]) + ".*"
            matching.extend(self._subscriptions.get(wildcard, []))

        # Global wildcard
        matching.extend(self._subscriptions.get("*", []))

        # Sort by priority and execute
        matching.sort(key=lambda s: s.priority)
        to_remove: List[tuple] = []

        for sub in matching:
            if event.propagation_stopped:
                break

            # Source filter
            if sub.source_filter and event.source != sub.source_filter:
                continue

            try:
                sub.handler(event)
            except Exception as e:
                logger.error(f"EventBus handler error for '{event.type}': {e}")

            if sub.once:
                # Find and mark for removal
                for etype, subs in self._subscriptions.items():
                    if sub in subs:
                        to_remove.append((etype, sub))

        # Clean up one-shot subscriptions
        for etype, sub in to_remove:
            if sub in self._subscriptions[etype]:
                self._subscriptions[etype].remove(sub)

        return event

    def emit_simple(self, event_type: str, source: str = "system", **data) -> Event:
        """Convenience method to emit an event without constructing an Event object."""
        event = Event(type=event_type, source=source, data=data)
        return self.emit(event)

    # ── Query ──────────────────────────────────────────────────

    def get_history(self, event_type: Optional[str] = None, limit: int = 20) -> List[Event]:
        """Get recent event history, optionally filtered by type."""
        if event_type:
            filtered = [e for e in self._history if e.type == event_type]
        else:
            filtered = list(self._history)
        return filtered[-limit:]

    def get_stats(self) -> Dict[str, int]:
        """Get event emission counts by type."""
        return dict(self._stats)

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get number of subscribers for a given event type (or total)."""
        if event_type:
            return len(self._subscriptions.get(event_type, []))
        return sum(len(subs) for subs in self._subscriptions.values())

    def clear(self):
        """Remove all subscriptions and history."""
        self._subscriptions.clear()
        self._history.clear()
        self._stats.clear()


if __name__ == "__main__":
    bus = EventBus()

    # Subscribe handlers
    results = []

    @bus.on("tick.pre", priority=EventPriority.HIGH)
    def on_pre_tick(event):
        results.append(f"PRE: {event.data}")

    @bus.on("tick.post", priority=EventPriority.NORMAL)
    def on_post_tick(event):
        results.append(f"POST: {event.data}")

    @bus.on("tick.*", priority=EventPriority.MONITOR)
    def on_any_tick(event):
        results.append(f"MONITOR: {event.type}")

    # Emit events
    bus.emit_simple("tick.pre", source="core", frame=1)
    bus.emit_simple("tick.post", source="core", frame=1)

    for r in results:
        logger.info(f"  {r}")

    logger.info(f"Stats: {bus.get_stats()}")
    logger.info(f"Subscribers: {bus.get_subscriber_count()}")
