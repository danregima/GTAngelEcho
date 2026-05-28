"""
Expression Snapshot Plugin — Captures avatar expression state at
configurable intervals and stores snapshots for analysis.

Demonstrates: Tick dispatch, hook usage, data collection.
"""
import time
import logging
from typing import Any, Dict, List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from extensions.plugin_registry import PluginBase, PluginMeta

logger = logging.getLogger("Plugin.ExprSnapshot")


class ExpressionSnapshotPlugin(PluginBase):
    """
    Captures periodic snapshots of the avatar expression state.
    Useful for analyzing emotional trajectories over time.
    """

    def __init__(self):
        self._snapshots: List[Dict] = []
        self._interval = 5
        self._max_snapshots = 200
        self._tick_count = 0

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="expression_snapshot",
            version="1.0.0",
            author="GTAngelEcho",
            description="Captures periodic snapshots of avatar expression state",
            hooks=["post_expression"],
            config_schema={
                "interval": {"type": "int", "default": 5},
                "max_snapshots": {"type": "int", "default": 200},
            }
        )

    def configure(self, config: Dict[str, Any]):
        self._interval = config.get("interval", 5)
        self._max_snapshots = config.get("max_snapshots", 200)

    def on_enable(self, context: Dict[str, Any]):
        logger.info(f"Expression Snapshot enabled (interval={self._interval})")

    def on_disable(self):
        logger.info(f"Expression Snapshot disabled ({len(self._snapshots)} snapshots captured)")

    def on_tick(self, tick_result: Dict[str, Any]):
        self._tick_count += 1
        if self._tick_count % self._interval != 0:
            return

        expression = tick_result.get("expression", {})
        if not expression:
            return

        snapshot = {
            "tick": tick_result.get("tick", 0),
            "timestamp": time.time(),
            "mode": tick_result.get("mode", "unknown"),
            "valence": tick_result.get("valence", 0),
            "arousal": tick_result.get("arousal", 0),
            "dominant_expression": expression.get("dominant_expression", "neutral"),
            "intensity": expression.get("intensity", 0),
            "action_units": expression.get("action_units", {}),
        }

        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

    def get_snapshots(self) -> List[Dict]:
        """Return all captured snapshots."""
        return list(self._snapshots)

    def get_expression_trajectory(self) -> List[Dict]:
        """Return a simplified trajectory of dominant expressions."""
        return [
            {
                "tick": s["tick"],
                "expression": s["dominant_expression"],
                "intensity": s["intensity"],
                "valence": s["valence"],
            }
            for s in self._snapshots
        ]


def create_plugin() -> PluginBase:
    """Factory function for plugin discovery."""
    return ExpressionSnapshotPlugin()
