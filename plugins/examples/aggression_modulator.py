"""
Aggression Modulator Plugin — Modifies action potentials based on
configurable aggression/pacifism bias.

Demonstrates: Hook system usage, data modification in the pipeline.
"""
import logging
from typing import Any, Dict

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from extensions.plugin_registry import PluginBase, PluginMeta
from extensions.hooks import HookPoint

logger = logging.getLogger("Plugin.Aggression")


class AggressionModulatorPlugin(PluginBase):
    """
    Modulates the aggression level of the cognitive architecture.

    Config:
        aggression_bias: float (-1.0 to 1.0)
            -1.0 = maximum pacifism (suppress engage, boost explore/socialize)
             0.0 = neutral (no modification)
            +1.0 = maximum aggression (boost engage, suppress retreat)
    """

    def __init__(self):
        self._hooks = None
        self._bias = 0.0

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="aggression_modulator",
            version="1.0.0",
            author="GTAngelEcho",
            description="Modulates action potentials with configurable aggression/pacifism bias",
            hooks=["post_synthesize"],
            config_schema={
                "aggression_bias": {"type": "float", "default": 0.0, "min": -1.0, "max": 1.0},
            }
        )

    def configure(self, config: Dict[str, Any]):
        self._bias = max(-1.0, min(1.0, config.get("aggression_bias", 0.0)))
        logger.info(f"Aggression bias set to: {self._bias:+.2f}")

    def on_enable(self, context: Dict[str, Any]):
        self._hooks = context.get("hooks")
        if self._hooks:
            self._hooks.add(
                HookPoint.POST_SYNTHESIZE,
                self._modulate_aggression,
                priority=20,
                name="aggression_modulator"
            )
        logger.info(f"Aggression Modulator enabled (bias={self._bias:+.2f})")

    def on_disable(self):
        if self._hooks:
            self._hooks.remove(HookPoint.POST_SYNTHESIZE, self._modulate_aggression)
        logger.info("Aggression Modulator disabled")

    def _modulate_aggression(self, synthesis_data):
        """Hook handler: modify action potentials based on bias."""
        if not isinstance(synthesis_data, dict):
            return synthesis_data

        potentials = synthesis_data.get("action_potentials", {})
        if not potentials:
            return synthesis_data

        if self._bias > 0:
            # Aggressive: boost engage, suppress retreat/socialize
            potentials["engage"] = potentials.get("engage", 0) * (1.0 + self._bias)
            potentials["retreat"] = potentials.get("retreat", 0) * (1.0 - self._bias * 0.5)
            potentials["socialize"] = potentials.get("socialize", 0) * (1.0 - self._bias * 0.3)
        elif self._bias < 0:
            # Pacifist: suppress engage, boost explore/socialize
            abs_bias = abs(self._bias)
            potentials["engage"] = potentials.get("engage", 0) * (1.0 - abs_bias * 0.7)
            potentials["explore"] = potentials.get("explore", 0) * (1.0 + abs_bias * 0.5)
            potentials["socialize"] = potentials.get("socialize", 0) * (1.0 + abs_bias * 0.5)

        synthesis_data["action_potentials"] = potentials
        return synthesis_data


def create_plugin() -> PluginBase:
    """Factory function for plugin discovery."""
    return AggressionModulatorPlugin()
