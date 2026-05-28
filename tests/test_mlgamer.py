"""Tests for the MLGamer module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_mlgamer_initialization():
    """Test MLGamer engine initializes correctly."""
    from mlgamer.trainer import MLGamerEngine
    engine = MLGamerEngine()
    assert engine.lr == 0.01
    assert engine.gamma == 0.95
    assert engine.epsilon == 0.2
    assert len(engine.q_table) == 0


def test_action_selection():
    """Test that action selection returns valid actions."""
    from mlgamer.trainer import MLGamerEngine, GameState
    engine = MLGamerEngine()
    state = GameState(health=100, ammo=30, nearby_enemies=1)
    action = engine.select_action(state)
    assert isinstance(action, str)
    assert action in ["patrol", "take_cover", "engage", "retreat", "flank", "heal", "reload", "loot"]


def test_learning():
    """Test that Q-values update after learning."""
    from mlgamer.trainer import MLGamerEngine, GameState
    engine = MLGamerEngine()
    state = GameState(health=100, nearby_enemies=1)
    next_state = GameState(health=90, nearby_enemies=0)
    
    engine.learn(state, "engage", 10.0, next_state)
    
    state_key = engine._encode_state(state)
    assert state_key in engine.q_table
    assert "engage" in engine.q_table[state_key]
    assert engine.q_table[state_key]["engage"] > 0


def test_opponent_modeling():
    """Test opponent model updates."""
    from mlgamer.trainer import MLGamerEngine
    engine = MLGamerEngine()
    
    engine.model_opponent("enemy_1", "rush", "hit")
    assert "enemy_1" in engine.opponent_models
    assert engine.opponent_models["enemy_1"].aggression > 0.5
    
    engine.model_opponent("enemy_1", "retreat", "miss")
    assert engine.opponent_models["enemy_1"].observations == 2


def test_strategy_evolution():
    """Test that strategy evolution decays epsilon."""
    from mlgamer.trainer import MLGamerEngine, GameState
    engine = MLGamerEngine(exploration_rate=0.5)
    
    # Fill experience buffer
    for i in range(101):
        engine.experience_buffer.append({"state": "s", "action": "a", "reward": 1.0, "next_state": "s2"})
    
    engine.evolve_strategy()
    assert engine.epsilon < 0.5


if __name__ == "__main__":
    test_mlgamer_initialization()
    test_action_selection()
    test_learning()
    test_opponent_modeling()
    test_strategy_evolution()
    print("All MLGamer tests passed!")
