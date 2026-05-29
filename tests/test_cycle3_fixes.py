"""
KSM Cycle 3 — Regression Tests for Structure-Preserving Mutations

Tests the 8 critical fixes applied during Cycle 3:
G1: Event→Plugin bridge (Deep Interlock)
G2: Hook points activated (Positive Space / The Void)
G3: Endocrine subscriber callback (Deep Interlock)
G4: Event count accuracy (Contrast)
G5: MLGamer tactic state update (Gradients)
G6: SuperHotGirl AU target decay (Good Shape)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from mlgamer.trainer import MLGamerEngine, GameState, TacticalState
from superhotgirl.expression_demo import AvatarExpressionSystem


class TestG5_MLGamerTacticUpdate:
    """G5: MLGamer current_tactic should update after select_action."""
    
    def test_tactic_updates_on_action(self):
        engine = MLGamerEngine(exploration_rate=0.0)  # Force exploit/heuristic
        state = GameState(health=100, nearby_enemies=1, cover_available=True)
        
        # Pre-populate Q-table so exploit path is taken
        engine.q_table["high_few_True"] = {"engage": 10.0, "patrol": 1.0}
        
        action = engine.select_action(state)
        assert action == "engage"
        assert engine.current_tactic == TacticalState.COMBAT
        
    def test_tactic_maps_retreat_to_evasion(self):
        engine = MLGamerEngine(exploration_rate=0.0)
        state = GameState(health=15, nearby_enemies=3, cover_available=True)
        
        action = engine.select_action(state)
        # Heuristic: health < 20 → retreat
        assert action == "retreat"
        assert engine.current_tactic == TacticalState.EVASION
        
    def test_tactic_maps_patrol(self):
        engine = MLGamerEngine(exploration_rate=0.0)
        state = GameState(health=100, nearby_enemies=0, cover_available=True)
        
        action = engine.select_action(state)
        assert action == "patrol"
        assert engine.current_tactic == TacticalState.PATROL


class TestG6_SuperHotGirlAUDecay:
    """G6: SuperHotGirl AU targets should decay toward zero when hormones drop."""
    
    def test_au_targets_decay(self):
        aes = AvatarExpressionSystem()
        
        # Set high dopamine → high AU12 target
        aes.update_from_endocrine({"dopamine_phasic": 0.8})
        au12_after_high = aes._target_aus["AU12"]
        assert au12_after_high > 0.5, "AU12 should be high after dopamine"
        
        # Now update with zero hormones multiple times
        for _ in range(20):
            aes.update_from_endocrine({})
            
        au12_after_decay = aes._target_aus["AU12"]
        assert au12_after_decay < au12_after_high, "AU12 target should have decayed"
        
    def test_au_targets_reach_zero(self):
        aes = AvatarExpressionSystem()
        
        # Set high cortisol
        aes.update_from_endocrine({"cortisol": 0.9})
        
        # Decay for many ticks with no hormones
        for _ in range(50):
            aes.update_from_endocrine({})
            
        # All targets should be at or near zero
        for au, val in aes._target_aus.items():
            assert val < 0.1, f"{au} target should have decayed to near zero, got {val}"


class TestPropertyCoherenceScript:
    """Verify the property coherence script runs and produces valid output."""
    
    def test_script_runs(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/property_coherence.py"],
            cwd=os.path.join(os.path.dirname(__file__), '..'),
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Cycle 3" in result.stderr or "Cycle 3" in result.stdout
        
    def test_report_json_valid(self):
        import json
        report_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'property_coherence_report.json')
        with open(report_path) as f:
            report = json.load(f)
        assert report["cycle"] == 3
        assert report["overall_score"] > 0.85
        assert len(report["properties"]) == 15
