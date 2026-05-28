"""
Telemetry Logger Plugin — Logs tick data, mode transitions, and events
to a structured JSON log file for offline analysis.

Demonstrates: Plugin lifecycle, event subscription, tick dispatch.
"""
import json
import time
import logging
from typing import Any, Dict
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from extensions.plugin_registry import PluginBase, PluginMeta

logger = logging.getLogger("Plugin.Telemetry")


class TelemetryLoggerPlugin(PluginBase):
    """Logs system telemetry to a JSON-lines file."""

    def __init__(self):
        self._log_path = None
        self._log_file = None
        self._event_bus = None
        self._tick_count = 0
        self._mode_transitions = 0
        self._last_mode = None

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="telemetry_logger",
            version="1.0.0",
            author="GTAngelEcho",
            description="Logs tick data and mode transitions to a JSON-lines file",
            events=["*"],  # Subscribe to all events
            hooks=["post_tick"],
            config_schema={
                "log_path": {"type": "string", "default": "telemetry.jsonl"},
                "log_interval": {"type": "int", "default": 1},
            }
        )

    def on_enable(self, context: Dict[str, Any]):
        config = context.get("config", {})
        self._log_path = config.get("log_path", "telemetry.jsonl")
        self._log_interval = config.get("log_interval", 1)
        self._event_bus = context.get("event_bus")

        # Open log file
        self._log_file = open(self._log_path, "a")
        logger.info(f"Telemetry logging to: {self._log_path}")

        # Subscribe to mode changes via event bus
        if self._event_bus:
            self._event_bus.on("endocrine.mode_change", self._on_mode_change)

    def on_disable(self):
        if self._log_file:
            self._log_file.close()
            self._log_file = None
        logger.info(f"Telemetry logger disabled ({self._tick_count} ticks logged)")

    def on_tick(self, tick_result: Dict[str, Any]):
        self._tick_count += 1
        if self._tick_count % self._log_interval != 0:
            return

        record = {
            "timestamp": time.time(),
            "tick": tick_result.get("tick", 0),
            "mode": tick_result.get("mode", "unknown"),
            "valence": tick_result.get("valence", 0),
            "arousal": tick_result.get("arousal", 0),
            "action": tick_result.get("action", "idle"),
            "cognitive_action": tick_result.get("cognitive_action", "idle"),
        }

        if self._log_file:
            self._log_file.write(json.dumps(record) + "\n")
            self._log_file.flush()

    def _on_mode_change(self, event):
        self._mode_transitions += 1
        if self._log_file:
            record = {
                "timestamp": time.time(),
                "event": "mode_change",
                "old_mode": event.data.get("old_mode", ""),
                "new_mode": event.data.get("new_mode", ""),
            }
            self._log_file.write(json.dumps(record) + "\n")
            self._log_file.flush()

    def on_event(self, event):
        """Log all events to the telemetry file."""
        if self._log_file and event.type != "tick.pre" and event.type != "tick.post":
            record = {
                "timestamp": time.time(),
                "event_type": event.type,
                "source": event.source,
                "data": {k: str(v)[:100] for k, v in event.data.items()},
            }
            self._log_file.write(json.dumps(record) + "\n")


def create_plugin() -> PluginBase:
    """Factory function for plugin discovery."""
    return TelemetryLoggerPlugin()
