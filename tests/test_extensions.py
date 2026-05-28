"""
Integration Tests for GTAngelEcho Extension Architecture (Cycle 2).
Tests EventBus, PluginRegistry, HookSystem, APIAdapter, and example plugins.
"""
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_event_bus_basic():
    """Test basic event emission and subscription."""
    from extensions.event_bus import EventBus, Event, EventPriority

    bus = EventBus()
    received = []

    bus.on("test.event", lambda e: received.append(e.data))
    bus.emit_simple("test.event", source="test", value=42)

    assert len(received) == 1
    assert received[0]["value"] == 42
    print("  ✓ EventBus basic emit/subscribe works")


def test_event_bus_priority():
    """Test that handlers execute in priority order."""
    from extensions.event_bus import EventBus, EventPriority

    bus = EventBus()
    order = []

    bus.on("test", lambda e: order.append("LOW"), priority=EventPriority.LOW)
    bus.on("test", lambda e: order.append("HIGH"), priority=EventPriority.HIGH)
    bus.on("test", lambda e: order.append("NORMAL"), priority=EventPriority.NORMAL)

    bus.emit_simple("test")
    assert order == ["HIGH", "NORMAL", "LOW"], f"Wrong order: {order}"
    print("  ✓ EventBus priority ordering correct")


def test_event_bus_wildcard():
    """Test wildcard subscriptions."""
    from extensions.event_bus import EventBus

    bus = EventBus()
    received = []

    bus.on("tick.*", lambda e: received.append(e.type))
    bus.emit_simple("tick.pre")
    bus.emit_simple("tick.post")
    bus.emit_simple("other.event")

    assert len(received) == 2
    assert "tick.pre" in received
    assert "tick.post" in received
    print("  ✓ EventBus wildcard subscriptions work")


def test_event_bus_once():
    """Test one-shot subscriptions."""
    from extensions.event_bus import EventBus

    bus = EventBus()
    count = [0]

    bus.once("test", lambda e: count.__setitem__(0, count[0] + 1))
    bus.emit_simple("test")
    bus.emit_simple("test")

    assert count[0] == 1, f"Expected 1, got {count[0]}"
    print("  ✓ EventBus one-shot subscription works")


def test_event_bus_cancellation():
    """Test event propagation stopping."""
    from extensions.event_bus import EventBus, EventPriority

    bus = EventBus()
    received = []

    def stopper(e):
        received.append("STOP")
        e.stop_propagation()

    bus.on("test", stopper, priority=EventPriority.HIGH)
    bus.on("test", lambda e: received.append("SHOULD_NOT_RUN"), priority=EventPriority.LOW)

    bus.emit_simple("test")
    assert received == ["STOP"]
    print("  ✓ EventBus propagation stopping works")


def test_hook_system():
    """Test hook system data modification."""
    from extensions.hooks import HookSystem, HookPoint

    hooks = HookSystem()

    def double_valence(data):
        if isinstance(data, dict) and "valence" in data:
            data["valence"] *= 2
        return data

    hooks.add(HookPoint.POST_TICK, double_valence, name="double_valence")

    result = hooks.apply(HookPoint.POST_TICK, {"valence": 0.5, "arousal": 0.3})
    assert result["valence"] == 1.0
    assert result["arousal"] == 0.3  # Unchanged
    print("  ✓ HookSystem data modification works")


def test_hook_system_priority():
    """Test hook handler priority ordering."""
    from extensions.hooks import HookSystem, HookPoint

    hooks = HookSystem()
    order = []

    hooks.add(HookPoint.PRE_TICK, lambda d: order.append("B") or d, priority=50)
    hooks.add(HookPoint.PRE_TICK, lambda d: order.append("A") or d, priority=10)
    hooks.add(HookPoint.PRE_TICK, lambda d: order.append("C") or d, priority=90)

    hooks.apply(HookPoint.PRE_TICK, {})
    assert order == ["A", "B", "C"]
    print("  ✓ HookSystem priority ordering correct")


def test_plugin_registry():
    """Test plugin registration and lifecycle."""
    from extensions.plugin_registry import PluginRegistry, PluginBase, PluginMeta

    class TestPlugin(PluginBase):
        def __init__(self):
            self.enabled = False
            self.ticks = 0

        def meta(self):
            return PluginMeta(name="test_plugin", version="1.0.0", description="Test")

        def on_enable(self, context):
            self.enabled = True

        def on_disable(self):
            self.enabled = False

        def on_tick(self, tick_result):
            self.ticks += 1

    registry = PluginRegistry()
    plugin = TestPlugin()

    assert registry.register(plugin)
    assert registry.total_count == 1

    assert registry.enable("test_plugin", {})
    assert plugin.enabled
    assert registry.enabled_count == 1

    registry.dispatch_tick({"tick": 1})
    assert plugin.ticks == 1

    assert registry.disable("test_plugin")
    assert not plugin.enabled
    print("  ✓ PluginRegistry lifecycle works")


def test_plugin_discovery():
    """Test plugin discovery from directory."""
    from extensions.plugin_registry import PluginRegistry

    registry = PluginRegistry()
    plugin_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins', 'examples')

    discovered = registry.discover(plugin_dir)
    assert len(discovered) >= 3, f"Expected >=3 plugins, got {len(discovered)}: {discovered}"
    assert "telemetry_logger" in discovered
    assert "aggression_modulator" in discovered
    assert "expression_snapshot" in discovered
    print(f"  ✓ Plugin discovery found {len(discovered)} plugins: {discovered}")


def test_api_adapter_routes():
    """Test API adapter route handling."""
    from extensions.api_adapter import GTAngelEchoAPI

    api = GTAngelEchoAPI()

    # Test route listing
    result = api.handle_request("GET", "/api/routes")
    assert result["status"] == 200
    assert len(result["data"]) > 10
    print(f"  ✓ API Adapter has {len(result['data'])} routes")


def test_api_adapter_404():
    """Test API adapter 404 handling."""
    from extensions.api_adapter import GTAngelEchoAPI

    api = GTAngelEchoAPI()
    result = api.handle_request("GET", "/api/nonexistent")
    assert result["status"] == 404
    print("  ✓ API Adapter returns 404 for unknown routes")


def test_api_adapter_with_system():
    """Test API adapter bound to a live system."""
    import importlib.util
    hub_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'gtangel', 'angel_echo.py')
    spec = importlib.util.spec_from_file_location('angel_echo', hub_path)
    hub_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hub_module)

    angel = hub_module.GTAngelEcho(autonomy_level=2)

    # Run a few ticks
    for _ in range(3):
        angel.game_tick(sensory_input={
            "visual": np.random.randn(8).tolist(),
            "auditory": np.random.randn(4).tolist(),
            "proprioceptive": np.random.randn(4).tolist(),
        })

    # Test state endpoint
    result = angel.api.handle_request("GET", "/api/state")
    assert result["status"] == 200
    assert result["data"]["tick"] == 3
    assert "hormones" in result["data"]
    print(f"  ✓ API /api/state returns live data (tick={result['data']['tick']})")

    # Test metrics endpoint
    result = angel.api.handle_request("GET", "/api/metrics")
    assert result["status"] == 200
    assert result["data"]["total_ticks"] == 3
    print(f"  ✓ API /api/metrics returns metrics")

    # Test event injection
    result = angel.api.handle_request("POST", "/api/event",
                                      {"type": "REWARD_RECEIVED", "intensity": 0.9})
    assert result["status"] == 200
    assert result["data"]["signaled"] == "REWARD_RECEIVED"
    print(f"  ✓ API /api/event injects events")


def test_full_pipeline_with_plugins():
    """Test the complete pipeline with plugins loaded."""
    import importlib.util
    hub_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'gtangel', 'angel_echo.py')
    spec = importlib.util.spec_from_file_location('angel_echo', hub_path)
    hub_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hub_module)

    plugin_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins', 'examples')
    angel = hub_module.GTAngelEcho(autonomy_level=2, plugin_dir=plugin_dir)

    # Run 10 ticks
    for i in range(10):
        angel.game_tick(
            world_events={"THREAT_DETECTED": 0.7} if i == 5 else None,
            sensory_input={
                "visual": np.random.randn(8).tolist(),
                "auditory": np.random.randn(4).tolist(),
                "proprioceptive": np.random.randn(4).tolist(),
            }
        )

    metrics = angel.get_metrics()
    assert metrics["total_ticks"] == 10
    assert metrics["plugins_enabled"] >= 3
    assert metrics["events_emitted"] > 0
    assert metrics["hooks_applied"] > 0
    print(f"  ✓ Full pipeline with {metrics['plugins_enabled']} plugins: "
          f"{metrics['events_emitted']} events, {metrics['hooks_applied']} hooks")


if __name__ == "__main__":
    print("=" * 60)
    print("  GTAngelEcho Extension Architecture Tests (Cycle 2)")
    print("=" * 60)

    tests = [
        ("EventBus: basic emit/subscribe", test_event_bus_basic),
        ("EventBus: priority ordering", test_event_bus_priority),
        ("EventBus: wildcard subscriptions", test_event_bus_wildcard),
        ("EventBus: one-shot subscription", test_event_bus_once),
        ("EventBus: propagation stopping", test_event_bus_cancellation),
        ("HookSystem: data modification", test_hook_system),
        ("HookSystem: priority ordering", test_hook_system_priority),
        ("PluginRegistry: lifecycle", test_plugin_registry),
        ("PluginRegistry: discovery", test_plugin_discovery),
        ("API Adapter: routes", test_api_adapter_routes),
        ("API Adapter: 404", test_api_adapter_404),
        ("API Adapter: live system", test_api_adapter_with_system),
        ("Full Pipeline with Plugins", test_full_pipeline_with_plugins),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            print(f"\n[TEST] {name}")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
