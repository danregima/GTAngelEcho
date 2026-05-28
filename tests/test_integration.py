"""
Integration Tests for GTAngelEcho
Tests the deep interlock between all 8 living centers.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_endocrine_full_16_channels():
    """Test that all 16 hormone channels are present and functional."""
    from endocrine.system import VirtualEndocrineSystem
    endo = VirtualEndocrineSystem()
    state = endo.get_state()
    
    expected_channels = [
        "CRH", "ACTH", "Cortisol", "Dopamine_Tonic", "Dopamine_Phasic",
        "Serotonin", "Norepinephrine", "Epinephrine", "Oxytocin",
        "T3", "T4", "Melatonin", "Insulin", "Glucagon", "IL6", "Anandamide"
    ]
    
    assert len(state) == 16, f"Expected 16 channels, got {len(state)}"
    for ch in expected_channels:
        assert ch in state, f"Missing channel: {ch}"
    print("  ✓ All 16 hormone channels present")


def test_endocrine_mode_transitions():
    """Test that cognitive modes transition correctly."""
    from endocrine.system import VirtualEndocrineSystem, CognitiveMode
    endo = VirtualEndocrineSystem()
    
    # Should start RESTING
    assert endo.current_mode == CognitiveMode.RESTING or endo.current_mode == CognitiveMode.CREATIVE
    
    # Threat should trigger STRESSED/VIGILANT/FOCUSED
    endo.signal_event("THREAT_DETECTED", 1.0)
    endo.tick()
    assert endo.current_mode in [CognitiveMode.STRESSED, CognitiveMode.VIGILANT, CognitiveMode.FOCUSED]
    print(f"  ✓ Threat → {endo.current_mode.value}")


def test_endocrine_valence_arousal():
    """Test valence-arousal mapping."""
    from endocrine.system import VirtualEndocrineSystem
    endo = VirtualEndocrineSystem()
    
    # Reward should increase valence
    endo.signal_event("REWARD_RECEIVED", 1.0)
    endo.tick()
    v, a = endo.get_valence_arousal()
    assert v > 0, f"Expected positive valence after reward, got {v}"
    print(f"  ✓ Reward → Valence={v:.2f}, Arousal={a:.2f}")


def test_endocrine_gland_fatigue():
    """Test that glands accumulate fatigue with repeated activation."""
    from endocrine.system import VirtualEndocrineSystem
    endo = VirtualEndocrineSystem()
    
    # Repeatedly activate same gland
    for _ in range(10):
        endo.signal_event("THREAT_DETECTED", 1.0)
    
    # Check fatigue accumulated
    hypothalamus_fatigue = endo.glands["hypothalamus"].fatigue
    assert hypothalamus_fatigue > 0, "Expected fatigue accumulation"
    print(f"  ✓ Gland fatigue after 10 activations: {hypothalamus_fatigue:.3f}")


def test_endocrine_subscriber():
    """Test subscriber notification system."""
    from endocrine.system import VirtualEndocrineSystem
    endo = VirtualEndocrineSystem()
    
    notifications = []
    endo.subscribe(lambda state, mode: notifications.append(mode))
    
    endo.signal_event("REWARD_RECEIVED", 0.8)
    endo.tick()
    
    assert len(notifications) == 1, f"Expected 1 notification, got {len(notifications)}"
    print(f"  ✓ Subscriber notified: {notifications[0].value}")


def test_reservoir_hierarchical_input_dim():
    """Test that HierarchicalESN exposes input_dim."""
    from reservoir.esn import HierarchicalESN
    hesn = HierarchicalESN(input_dim=16, layer_dims=(64, 32), output_dim=32)
    assert hesn.input_dim == 16
    output = hesn.step(np.random.randn(16))
    assert output.shape == (32,)
    print(f"  ✓ HierarchicalESN: input_dim=16, output shape={output.shape}")


def test_memory_store_and_recall():
    """Test memory convenience methods."""
    from cognitive.memory import CognitiveMemorySystem
    mem = CognitiveMemorySystem()
    
    mem.store_episodic({"action": "engage", "result": "victory"}, valence=0.8)
    mem.store_episodic({"action": "retreat", "result": "escape"}, valence=-0.3)
    
    assert len(mem.episodic_memory) == 2
    
    recalls = mem.recall_episodic(top_k=5)
    assert len(recalls) == 2
    assert recalls[0]["valence"] == 0.8 or recalls[1]["valence"] == 0.8
    print(f"  ✓ Memory store/recall: {len(recalls)} episodes retrieved")


def test_superhotgirl_expression_state():
    """Test that SuperHotGirl exports expression state."""
    from superhotgirl.expression_demo import AvatarExpressionSystem
    aes = AvatarExpressionSystem()
    
    aes.update_from_endocrine({"cortisol": 0.1, "dopamine_phasic": 0.8, "serotonin": 0.5})
    aes.apply_chaotic_micro_expressions()
    aes.apply_aesthetic_bias()
    
    state = aes.get_expression_state()
    assert "action_units" in state
    assert "dominant_expression" in state
    assert "intensity" in state
    assert state["dominant_expression"] in ["joy", "anger", "surprise", "fear", "disgust", "sadness", "neutral"]
    print(f"  ✓ Expression state: dominant={state['dominant_expression']}, intensity={state['intensity']:.3f}")


def test_superhotgirl_lorenz_chaos():
    """Test that Lorenz attractor produces bounded perturbations."""
    from superhotgirl.expression_demo import LorenzState
    lorenz = LorenzState()
    
    perturbations = [lorenz.get_perturbation(0.1) for _ in range(100)]
    assert all(-0.1 <= p <= 0.1 for p in perturbations), "Perturbations out of bounds"
    assert len(set(round(p, 6) for p in perturbations)) > 10, "Perturbations not diverse enough"
    print(f"  ✓ Lorenz chaos: range=[{min(perturbations):.4f}, {max(perturbations):.4f}]")


def test_cognitive_core_echobeats():
    """Test the full Echobeats cycle with interlocked modules."""
    import importlib.util
    from endocrine.system import VirtualEndocrineSystem
    from reservoir.esn import EchoStateNetwork
    from cognitive.memory import CognitiveMemorySystem
    
    # Load cognitive_loop from hyphenated directory
    dte_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'deep-tree-echo', 'cognitive_loop.py')
    spec = importlib.util.spec_from_file_location('cognitive_loop', dte_path)
    dte_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dte_module)
    
    endo = VirtualEndocrineSystem()
    esn = EchoStateNetwork(input_dim=8, reservoir_dim=64, output_dim=32)
    memory = CognitiveMemorySystem()
    
    core = dte_module.CognitiveCore(reservoir=esn, memory=memory, endocrine=endo)
    
    # Run a cycle with threat input
    endo.signal_event("THREAT_DETECTED", 0.8)
    endo.tick()
    
    result = core.run_echobeats_cycle({
        "visual": [0.9, 0.8, 0.7, 0.6, 0.1, 0.1, 0.1, 0.1],
        "auditory": [0.5, 0.3, 0.1, 0.0],
        "proprioceptive": [0.2, 0.2, 0.1, 0.0]
    })
    
    assert result.selected_action in ["engage", "retreat", "explore", "loot", "patrol", "socialize", "idle"]
    assert "posture" in result.embodiment_update
    print(f"  ✓ Echobeats cycle: action={result.selected_action}, posture={result.embodiment_update['posture']}")


def test_full_integration_pipeline():
    """Test the complete GTAngelEcho integration pipeline."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    import importlib.util
    hub_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'gtangel', 'angel_echo.py')
    spec = importlib.util.spec_from_file_location('angel_echo', hub_path)
    hub_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hub_module)
    
    angel = hub_module.GTAngelEcho(autonomy_level=2)
    
    # Run 5 ticks
    for i in range(5):
        result = angel.game_tick(
            world_events={"THREAT_DETECTED": 0.5} if i == 2 else None,
            sensory_input={
                "visual": np.random.randn(8).tolist(),
                "auditory": np.random.randn(4).tolist(),
                "proprioceptive": np.random.randn(4).tolist(),
            }
        )
        
    assert result["tick"] == 5
    assert "mode" in result
    assert "valence" in result
    assert "arousal" in result
    assert "action" in result
    
    metrics = angel.get_metrics()
    assert metrics["total_ticks"] == 5
    assert metrics["actions_taken"] == 5
    print(f"  ✓ Full pipeline: 5 ticks, mode={result['mode']}, action={result['action']}")


if __name__ == "__main__":
    print("=" * 60)
    print("  GTAngelEcho Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Endocrine: 16 channels", test_endocrine_full_16_channels),
        ("Endocrine: mode transitions", test_endocrine_mode_transitions),
        ("Endocrine: valence-arousal", test_endocrine_valence_arousal),
        ("Endocrine: gland fatigue", test_endocrine_gland_fatigue),
        ("Endocrine: subscriber", test_endocrine_subscriber),
        ("Reservoir: hierarchical input_dim", test_reservoir_hierarchical_input_dim),
        ("Memory: store and recall", test_memory_store_and_recall),
        ("SuperHotGirl: expression state", test_superhotgirl_expression_state),
        ("SuperHotGirl: Lorenz chaos", test_superhotgirl_lorenz_chaos),
        ("Cognitive Core: Echobeats", test_cognitive_core_echobeats),
        ("Full Integration Pipeline", test_full_integration_pipeline),
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
            failed += 1
            
    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")
    
    if failed > 0:
        sys.exit(1)
