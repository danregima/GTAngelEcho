"""
MLGamer - Adaptive Gameplay Intelligence
Reinforcement learning, opponent modeling, and tactical decision-making for game AI.
"""
import logging
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("MLGamer")


class TacticalState(Enum):
    PATROL = "patrol"
    COMBAT = "combat"
    EVASION = "evasion"
    LOOTING = "looting"
    SOCIAL = "social"
    STEALTH = "stealth"


@dataclass
class OpponentModel:
    """Model of an observed opponent's behavior patterns."""
    id: str
    aggression: float = 0.5
    skill_level: float = 0.5
    preferred_range: str = "medium"
    weapon_preference: str = "unknown"
    observations: int = 0
    
    def update(self, action_observed: str, outcome: str):
        """Update opponent model based on observed behavior."""
        self.observations += 1
        if action_observed == "rush":
            self.aggression = min(1.0, self.aggression + 0.1)
        elif action_observed == "retreat":
            self.aggression = max(0.0, self.aggression - 0.1)


@dataclass
class GameState:
    """Current game state representation."""
    health: float = 100.0
    ammo: int = 30
    position: tuple = (0.0, 0.0, 0.0)
    nearby_enemies: int = 0
    nearby_allies: int = 0
    cover_available: bool = True
    time_of_day: float = 12.0  # 24h format
    wanted_level: int = 0


class MLGamerEngine:
    """
    Adaptive gameplay AI combining:
    - Q-learning for tactical decisions
    - Opponent modeling for prediction
    - Strategy evolution through experience
    """
    
    def __init__(self, learning_rate=0.01, discount_factor=0.95, exploration_rate=0.2):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.opponent_models: Dict[str, OpponentModel] = {}
        self.experience_buffer: List[dict] = []
        self.current_tactic = TacticalState.PATROL
        self.total_reward = 0.0
        self.episodes = 0
        logger.info("MLGamer Engine initialized (RL + Opponent Modeling + Strategy Evolution)")
        
    def select_action(self, game_state: GameState) -> str:
        """Select tactical action based on current state and learned policy."""
        state_key = self._encode_state(game_state)
        
        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            action = random.choice(self._available_actions(game_state))
            logger.info(f"[Explore] Selected action: {action}")
        else:
            # Exploit learned Q-values
            if state_key in self.q_table:
                action = max(self.q_table[state_key], key=self.q_table[state_key].get)
                logger.info(f"[Exploit] Selected action: {action}")
            else:
                action = self._heuristic_action(game_state)
                logger.info(f"[Heuristic] Selected action: {action}")
                
        # Update current tactic state based on selected action
        try:
            # Try to map action string to TacticalState enum
            for state in TacticalState:
                if state.value == action:
                    self.current_tactic = state
                    break
            else:
                # Map specific actions to broader tactical states
                if action in ["engage", "flank"]:
                    self.current_tactic = TacticalState.COMBAT
                elif action in ["take_cover", "retreat", "heal", "reload"]:
                    self.current_tactic = TacticalState.EVASION
                elif action == "loot":
                    self.current_tactic = TacticalState.LOOTING
                else:
                    self.current_tactic = TacticalState.PATROL
        except Exception:
            pass
            
        return action
        
    def _available_actions(self, state: GameState) -> List[str]:
        """Determine available actions based on game state."""
        actions = ["patrol", "take_cover", "engage", "retreat", "flank"]
        if state.health < 30:
            actions.append("heal")
        if state.ammo < 5:
            actions.append("reload")
        if state.nearby_enemies == 0:
            actions.append("loot")
        return actions
        
    def _heuristic_action(self, state: GameState) -> str:
        """Fallback heuristic when no Q-values available."""
        if state.health < 20:
            return "retreat"
        if state.nearby_enemies > 2 and state.cover_available:
            return "take_cover"
        if state.nearby_enemies == 1:
            return "engage"
        return "patrol"
        
    def _encode_state(self, state: GameState) -> str:
        """Encode game state into a hashable key for Q-table."""
        health_bin = "low" if state.health < 30 else "mid" if state.health < 70 else "high"
        enemies_bin = "none" if state.nearby_enemies == 0 else "few" if state.nearby_enemies < 3 else "many"
        return f"{health_bin}_{enemies_bin}_{state.cover_available}"
        
    def learn(self, state: GameState, action: str, reward: float, next_state: GameState):
        """Update Q-values from experience."""
        state_key = self._encode_state(state)
        next_key = self._encode_state(next_state)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if action not in self.q_table[state_key]:
            self.q_table[state_key][action] = 0.0
            
        # Q-learning update
        max_next_q = max(self.q_table.get(next_key, {"_": 0.0}).values())
        td_error = reward + self.gamma * max_next_q - self.q_table[state_key][action]
        self.q_table[state_key][action] += self.lr * td_error
        
        self.total_reward += reward
        self.experience_buffer.append({
            "state": state_key, "action": action,
            "reward": reward, "next_state": next_key
        })
        
    def model_opponent(self, opponent_id: str, action: str, outcome: str):
        """Update opponent model with new observation."""
        if opponent_id not in self.opponent_models:
            self.opponent_models[opponent_id] = OpponentModel(id=opponent_id)
        self.opponent_models[opponent_id].update(action, outcome)
        
    def get_tactical_state(self) -> TacticalState:
        """Return current tactical state."""
        return self.current_tactic
        
    def evolve_strategy(self):
        """Periodically evolve the strategy based on accumulated experience."""
        if len(self.experience_buffer) > 100:
            # Decay exploration rate
            self.epsilon = max(0.05, self.epsilon * 0.99)
            logger.info(f"Strategy evolved. Epsilon: {self.epsilon:.3f}, Total Reward: {self.total_reward:.1f}")
            self.episodes += 1


def run_training_session(env_name="urban_combat", episodes=100):
    """Run a training session for the MLGamer."""
    logger.info(f"Starting MLGamer training: env={env_name}, episodes={episodes}")
    
    engine = MLGamerEngine()
    
    for ep in range(episodes):
        state = GameState(
            health=100.0,
            ammo=30,
            nearby_enemies=random.randint(0, 4),
            cover_available=random.random() > 0.3
        )
        
        for step in range(50):
            action = engine.select_action(state)
            
            # Simulate environment response
            reward = _simulate_reward(state, action)
            next_state = _simulate_transition(state, action)
            
            engine.learn(state, action, reward, next_state)
            state = next_state
            
            if state.health <= 0:
                break
                
        engine.evolve_strategy()
        
        if (ep + 1) % 10 == 0:
            logger.info(f"Episode {ep+1}/{episodes} | Total Reward: {engine.total_reward:.1f} | Epsilon: {engine.epsilon:.3f}")
            
    logger.info(f"Training complete. Q-table size: {len(engine.q_table)}")
    return engine


def _simulate_reward(state: GameState, action: str) -> float:
    """Simulate reward from environment."""
    if action == "engage" and state.nearby_enemies > 0:
        return 10.0 if random.random() > 0.4 else -5.0
    if action == "retreat" and state.health < 30:
        return 5.0
    if action == "take_cover" and state.nearby_enemies > 2:
        return 3.0
    return -0.1  # Small penalty for time


def _simulate_transition(state: GameState, action: str) -> GameState:
    """Simulate state transition."""
    new_state = GameState(
        health=state.health - random.uniform(0, 10) if state.nearby_enemies > 0 else state.health,
        ammo=max(0, state.ammo - (3 if action == "engage" else 0)),
        nearby_enemies=max(0, state.nearby_enemies + random.randint(-1, 1)),
        cover_available=random.random() > 0.3
    )
    return new_state


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MLGamer Training")
    parser.add_argument("--env", default="urban_combat", help="Training environment")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes")
    args = parser.parse_args()
    
    run_training_session(args.env, args.episodes)
