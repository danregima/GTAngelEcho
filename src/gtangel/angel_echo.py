"""
GTAngelEcho Integration Hub — Full Deep Interlock
Binds all 8 living centers into a unified per-tick pipeline.

KSM Cycle 1: Strengthened Deep Interlock (Property 8) and Alternating Repetition (Property 4).
"""
import sys
import os
import time
import logging
import numpy as np
from typing import Dict, Optional

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from endocrine.system import VirtualEndocrineSystem, CognitiveMode
from reservoir.esn import EchoStateNetwork, HierarchicalESN
from cognitive.memory import CognitiveMemorySystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("GTAngelEcho")


class GTAngelEcho:
    """
    GTAngelEcho Unified Architecture — Integration Hub.
    
    Connects all 8 living centers in a per-tick pipeline:
    1. World Events → Endocrine System
    2. Endocrine Tick → Hormone decay + mode detection
    3. Reservoir Step → ESN temporal embedding
    4. Cognitive Cycle → Echobeats 4-phase
    5. Memory Update → Store/retrieve
    6. MLGamer Decision → Tactical action selection
    7. GTAngel Navigation → Pathfinding + mission progress
    8. Avatar Expression → FACS + chaos + aesthetics
    9. Avatar Embodiment → 4E body state
    
    Composition: GTAngel ⊗ DeepTreeEcho(SuperHotGirl ⊕ MLGamer)
    """
    
    def __init__(self, autonomy_level: int = 2):
        logger.info("=" * 60)
        logger.info("  GTAngelEcho Unified Architecture — Booting...")
        logger.info("=" * 60)
        
        self.autonomy_level = autonomy_level
        self.tick_count = 0
        
        # Center 5: Emotional Dynamics (full 16-channel)
        self.endocrine = VirtualEndocrineSystem()
        
        # Center 6: Reservoir Computing (hierarchical ESN)
        self.reservoir = HierarchicalESN(
            input_dim=16, layer_dims=(64, 32), output_dim=32
        )
        
        # Center 7: Memory Systems
        self.memory = CognitiveMemorySystem()
        
        # Center 1: Cognitive Core (with deep interlock)
        import importlib.util
        dte_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'deep-tree-echo', 'cognitive_loop.py')
        spec = importlib.util.spec_from_file_location('cognitive_loop', dte_path)
        dte_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dte_module)
        self.cognition = dte_module.CognitiveCore(
            reservoir=self.reservoir,
            memory=self.memory,
            endocrine=self.endocrine
        )
        
        # Center 2: Avatar Expression (SuperHotGirl)
        try:
            from superhotgirl.expression_demo import AvatarExpressionSystem
            self.avatar_expression = AvatarExpressionSystem()
        except ImportError:
            self.avatar_expression = None
            logger.warning("SuperHotGirl module not available (scaffold)")
            
        # Center 8: Avatar Embodiment
        try:
            from avatar.embodiment import AvatarEmbodiment
            self.avatar_embodiment = AvatarEmbodiment()
        except ImportError:
            self.avatar_embodiment = None
            logger.warning("Avatar Embodiment module not available (scaffold)")
            
        # Center 3: Gameplay Intelligence (MLGamer)
        try:
            from mlgamer.trainer import MLGamerEngine, GameState
            self.mlgamer = MLGamerEngine()
            self._GameState = GameState
        except ImportError:
            self.mlgamer = None
            self._GameState = None
            logger.warning("MLGamer module not available (scaffold)")
            
        # Center 4: World Navigation (GTAngel)
        try:
            from gtangel.navigation import GTAngelNavigator
            self.navigator = GTAngelNavigator()
        except ImportError:
            self.navigator = None
            logger.warning("GTAngel Navigator not available (scaffold)")
            
        # Register endocrine subscriber for cross-module updates
        self.endocrine.subscribe(self._on_endocrine_update)
        
        # Performance metrics
        self.metrics = {
            "total_ticks": 0,
            "mode_transitions": 0,
            "actions_taken": 0,
            "memories_stored": 0,
            "missions_completed": 0,
        }
        
        logger.info(f"Architecture booted at Autonomy Level {self.autonomy_level}")
        logger.info(f"Centers active: Endocrine=✓ Reservoir=✓ Memory=✓ Cognition=✓ "
                   f"Expression={'✓' if self.avatar_expression else '○'} "
                   f"Embodiment={'✓' if self.avatar_embodiment else '○'} "
                   f"MLGamer={'✓' if self.mlgamer else '○'} "
                   f"Navigator={'✓' if self.navigator else '○'}")
        logger.info("=" * 60)
        
    def game_tick(self, world_events: Optional[Dict] = None, sensory_input: Optional[Dict] = None) -> Dict:
        """
        Main integration loop — executed per game frame/tick.
        
        Args:
            world_events: Dict of events from the game world
            sensory_input: Dict of sensory data (visual, auditory, proprioceptive)
            
        Returns:
            Dict with tick results (action, mode, avatar state, navigation state)
        """
        self.tick_count += 1
        self.metrics["total_ticks"] += 1
        
        # === Step 1: World Events → Endocrine ===
        if world_events:
            for event_type, intensity in world_events.items():
                self.endocrine.signal_event(event_type, intensity, source="world")
                
        # === Step 2: Endocrine Tick ===
        old_mode = self.endocrine.current_mode
        self.endocrine.tick()
        if self.endocrine.current_mode != old_mode:
            self.metrics["mode_transitions"] += 1
            
        # === Step 3: Cognitive Cycle (includes Reservoir + Memory interlock) ===
        enactment = self.cognition.run_echobeats_cycle(sensory_input)
        self.metrics["actions_taken"] += 1
        
        # === Step 4: MLGamer Tactical Decision ===
        tactical_action = enactment.selected_action
        if self.mlgamer and self._GameState:
            hormone_state = self.endocrine.get_state()
            game_state = self._GameState(
                health=100,  # Would come from game engine
                ammo=30,
                nearby_enemies=1 if enactment.selected_action == "engage" else 0,
                cover_available=enactment.embodiment_update.get("posture") == "defensive",
                wanted_level=0
            )
            tactical_action = self.mlgamer.select_action(game_state)
            
        # === Step 5: Navigation Update ===
        nav_state = {}
        if self.navigator:
            nav_state = self.navigator.tick()
            if self.navigator.current_mission and self.navigator.current_mission.completed:
                self.metrics["missions_completed"] += 1
                self.endocrine.signal_event("MISSION_COMPLETE", 0.8, source="navigator")
                
        # === Step 6: Avatar Expression ===
        expression_state = {}
        if self.avatar_expression:
            hormone_state = self.endocrine.get_state()
            avatar_endo = {
                "cortisol": hormone_state.get("Cortisol", 0.15),
                "dopamine_phasic": hormone_state.get("Dopamine_Phasic", 0.0),
                "oxytocin": hormone_state.get("Oxytocin", 0.1),
                "norepinephrine": hormone_state.get("Norepinephrine", 0.1),
                "serotonin": hormone_state.get("Serotonin", 0.4),
            }
            self.avatar_expression.update_from_endocrine(avatar_endo)
            self.avatar_expression.apply_chaotic_micro_expressions()
            self.avatar_expression.apply_aesthetic_bias()
            expression_state = self.avatar_expression.get_expression_state()
            
        # === Step 7: Avatar Embodiment ===
        embodiment_state = {}
        if self.avatar_embodiment:
            self.avatar_embodiment.update_from_cognitive_mode(
                self.endocrine.current_mode.value,
                self.endocrine.get_state()
            )
            # Detect affordances from nav environment
            if self.navigator:
                env = self.navigator.scan_environment()
                self.avatar_embodiment.detect_affordances({
                    "cover_nearby": any(v.get("danger", 0) > 0.5 for v in env.values()),
                    "vehicle_nearby": False,
                    "npc_nearby": any(v.get("distance", 100) < 10 for v in env.values()),
                })
            embodiment_state = self.avatar_embodiment.get_embodiment_state()
            
        # === Compile Tick Result ===
        valence, arousal = self.endocrine.get_valence_arousal()
        
        result = {
            "tick": self.tick_count,
            "mode": self.endocrine.current_mode.value,
            "valence": valence,
            "arousal": arousal,
            "action": tactical_action,
            "cognitive_action": enactment.selected_action,
            "navigation": nav_state,
            "expression": expression_state,
            "embodiment": embodiment_state,
        }
        
        if self.tick_count % 10 == 0:
            logger.info(f"[Tick {self.tick_count}] Mode={result['mode']} "
                       f"V={valence:.2f} A={arousal:.2f} Action={tactical_action}")
                       
        return result
        
    def _on_endocrine_update(self, state: Dict, mode: CognitiveMode):
        """Callback from endocrine system on state change."""
        # Could trigger avatar micro-expression updates here
        pass
        
    def get_metrics(self) -> Dict:
        """Return performance metrics."""
        return {
            **self.metrics,
            "current_mode": self.endocrine.current_mode.value,
            "mode_stability": self.endocrine.mode_stability,
            "memory_count": len(self.memory.episodic_memory),
            "autonomy_level": self.autonomy_level,
        }
        
    def run_simulation(self, ticks: int = 50, verbose: bool = False):
        """Run a full simulation for N ticks with random events."""
        import random
        
        logger.info(f"\n{'='*60}")
        logger.info(f"  Running GTAngelEcho Simulation ({ticks} ticks)")
        logger.info(f"{'='*60}\n")
        
        event_types = [
            "THREAT_DETECTED", "REWARD_RECEIVED", "COMBAT_HIT",
            "COMBAT_VICTORY", "MISSION_COMPLETE", "EXPLORATION_DISCOVERY",
            "SOCIAL_BOND", "STEALTH_SUCCESS"
        ]
        
        for t in range(ticks):
            # Random world events
            world_events = {}
            if random.random() < 0.2:
                event = random.choice(event_types)
                world_events[event] = random.uniform(0.3, 1.0)
                
            # Random sensory input
            sensory = {
                "visual": np.random.randn(8).tolist(),
                "auditory": np.random.randn(4).tolist(),
                "proprioceptive": np.random.randn(4).tolist(),
            }
            
            result = self.game_tick(world_events, sensory)
            
            if verbose and t % 5 == 0:
                logger.info(f"  t={t}: mode={result['mode']}, action={result['action']}, "
                           f"V={result['valence']:.2f}, A={result['arousal']:.2f}")
                           
        # Final report
        metrics = self.get_metrics()
        logger.info(f"\n{'='*60}")
        logger.info(f"  Simulation Complete")
        logger.info(f"{'='*60}")
        logger.info(f"  Ticks: {metrics['total_ticks']}")
        logger.info(f"  Mode Transitions: {metrics['mode_transitions']}")
        logger.info(f"  Actions Taken: {metrics['actions_taken']}")
        logger.info(f"  Memories Stored: {metrics['memory_count']}")
        logger.info(f"  Final Mode: {metrics['current_mode']}")
        logger.info(f"  Autonomy Level: {metrics['autonomy_level']}")
        logger.info(f"{'='*60}\n")
        
        return metrics


if __name__ == "__main__":
    angel = GTAngelEcho(autonomy_level=2)
    metrics = angel.run_simulation(ticks=30, verbose=True)
