"""
Virtual Endocrine System — Full 16-Channel SIMD Bus
Biologically-inspired emotional dynamics with 10 virtual glands and 16 hormone channels.
Implements exponential decay, cross-gland cascades, and emergent cognitive mode detection.

KSM Cycle 1 Target: Strengthen this center from scaffold to functional.
"""
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("EndocrineSystem")


class CognitiveMode(Enum):
    """Emergent cognitive modes from hormone space."""
    RESTING = "RESTING"
    STRESSED = "STRESSED"
    REWARD = "REWARD"
    SOCIAL = "SOCIAL"
    FOCUSED = "FOCUSED"
    CREATIVE = "CREATIVE"
    VIGILANT = "VIGILANT"
    EXHAUSTED = "EXHAUSTED"


@dataclass
class HormoneChannel:
    """A single hormone channel in the 16-channel bus."""
    name: str
    value: float = 0.0
    baseline: float = 0.0
    decay_rate: float = 0.05
    min_val: float = 0.0
    max_val: float = 1.0
    gland_source: str = ""
    
    def decay(self, dt: float = 1.0):
        """Exponential decay toward baseline."""
        diff = self.value - self.baseline
        self.value -= diff * self.decay_rate * dt
        self.value = max(self.min_val, min(self.max_val, self.value))
        
    def release(self, amount: float):
        """Release hormone (add to current value, clamped)."""
        self.value = min(self.max_val, self.value + amount)
        
    def suppress(self, amount: float):
        """Suppress hormone (subtract from current value, clamped)."""
        self.value = max(self.min_val, self.value - amount)


@dataclass
class VirtualGland:
    """A virtual gland that produces hormones in response to stimuli."""
    name: str
    target_hormones: List[str]
    sensitivity: float = 1.0
    fatigue: float = 0.0
    fatigue_rate: float = 0.01
    recovery_rate: float = 0.005
    active: bool = True
    
    def activate(self, intensity: float) -> Dict[str, float]:
        """Activate gland and return hormone release amounts."""
        if not self.active:
            return {}
            
        # Fatigue reduces output
        effective_intensity = intensity * self.sensitivity * (1.0 - self.fatigue)
        
        # Accumulate fatigue
        self.fatigue = min(1.0, self.fatigue + self.fatigue_rate * intensity)
        
        releases = {}
        for hormone in self.target_hormones:
            releases[hormone] = effective_intensity
        return releases
        
    def recover(self, dt: float = 1.0):
        """Recover from fatigue over time."""
        self.fatigue = max(0.0, self.fatigue - self.recovery_rate * dt)


class VirtualEndocrineSystem:
    """
    Full 16-Channel Virtual Endocrine System.
    
    Implements:
    - 16 hormone channels (SIMD-style parallel processing)
    - 10 virtual glands with fatigue and recovery
    - Cross-gland cascade effects (HPA axis, etc.)
    - Emergent cognitive mode detection via centroid classification
    - Event history for temporal pattern analysis
    - Hormone bus subscribers for inter-module communication
    """
    
    def __init__(self):
        # Initialize 16 hormone channels
        self.channels: Dict[str, HormoneChannel] = self._init_channels()
        
        # Initialize 10 virtual glands
        self.glands: Dict[str, VirtualGland] = self._init_glands()
        
        # Cognitive mode
        self.current_mode: CognitiveMode = CognitiveMode.RESTING
        self.mode_history: List[Tuple[float, CognitiveMode]] = []
        self.mode_stability: float = 0.0  # How long in current mode
        
        # Event history
        self.event_history: List[Dict] = []
        self.tick_count: int = 0
        
        # Subscribers (other modules can register callbacks)
        self._subscribers: List[Callable] = []
        
        # Cascade rules (gland A activation triggers gland B)
        self._cascades: Dict[str, List[Tuple[str, float, float]]] = {
            # HPA Axis: CRH → ACTH → Cortisol
            "hypothalamus": [("pituitary_anterior", 0.6, 0.3)],
            "pituitary_anterior": [("adrenal_cortex", 0.5, 0.5)],
            # Sympathetic: Norepinephrine → Epinephrine
            "locus_coeruleus": [("adrenal_medulla", 0.4, 0.2)],
        }
        
        logger.info("Virtual Endocrine System initialized: 16 channels, 10 glands")
        
    def _init_channels(self) -> Dict[str, HormoneChannel]:
        """Initialize all 16 hormone channels."""
        return {
            # HPA Axis (Stress)
            "CRH": HormoneChannel("CRH", 0.05, 0.05, 0.10, gland_source="hypothalamus"),
            "ACTH": HormoneChannel("ACTH", 0.05, 0.05, 0.08, gland_source="pituitary_anterior"),
            "Cortisol": HormoneChannel("Cortisol", 0.15, 0.15, 0.02, gland_source="adrenal_cortex"),
            # Dopaminergic (Reward/Motivation)
            "Dopamine_Tonic": HormoneChannel("Dopamine_Tonic", 0.30, 0.30, 0.03, gland_source="vta"),
            "Dopamine_Phasic": HormoneChannel("Dopamine_Phasic", 0.0, 0.0, 0.20, gland_source="vta"),
            # Serotonergic (Mood/Satiety)
            "Serotonin": HormoneChannel("Serotonin", 0.40, 0.40, 0.01, gland_source="raphe_nuclei"),
            # Noradrenergic (Arousal/Vigilance)
            "Norepinephrine": HormoneChannel("Norepinephrine", 0.10, 0.10, 0.08, gland_source="locus_coeruleus"),
            "Epinephrine": HormoneChannel("Epinephrine", 0.05, 0.05, 0.12, gland_source="adrenal_medulla"),
            # Oxytocinergic (Social Bonding)
            "Oxytocin": HormoneChannel("Oxytocin", 0.10, 0.10, 0.04, gland_source="hypothalamus"),
            # Thyroid (Metabolic Rate / Energy)
            "T3": HormoneChannel("T3", 0.50, 0.50, 0.005, gland_source="thyroid"),
            "T4": HormoneChannel("T4", 0.50, 0.50, 0.003, gland_source="thyroid"),
            # Circadian (Sleep/Wake)
            "Melatonin": HormoneChannel("Melatonin", 0.20, 0.20, 0.02, gland_source="pineal"),
            # Pancreatic (Energy Regulation)
            "Insulin": HormoneChannel("Insulin", 0.30, 0.30, 0.04, gland_source="pancreas"),
            "Glucagon": HormoneChannel("Glucagon", 0.20, 0.20, 0.04, gland_source="pancreas"),
            # Immune (Inflammation)
            "IL6": HormoneChannel("IL6", 0.05, 0.05, 0.06, gland_source="immune"),
            # Endocannabinoid (Homeostasis/Pleasure)
            "Anandamide": HormoneChannel("Anandamide", 0.25, 0.25, 0.05, gland_source="endocannabinoid"),
        }
        
    def _init_glands(self) -> Dict[str, VirtualGland]:
        """Initialize all 10 virtual glands."""
        return {
            "hypothalamus": VirtualGland("Hypothalamus", ["CRH", "Oxytocin"], sensitivity=1.0),
            "pituitary_anterior": VirtualGland("Pituitary (Anterior)", ["ACTH"], sensitivity=0.8),
            "adrenal_cortex": VirtualGland("Adrenal Cortex", ["Cortisol"], sensitivity=0.7, fatigue_rate=0.02),
            "adrenal_medulla": VirtualGland("Adrenal Medulla", ["Epinephrine"], sensitivity=0.9),
            "vta": VirtualGland("VTA (Dopamine)", ["Dopamine_Tonic", "Dopamine_Phasic"], sensitivity=1.0),
            "raphe_nuclei": VirtualGland("Raphe Nuclei", ["Serotonin"], sensitivity=0.6, fatigue_rate=0.005),
            "locus_coeruleus": VirtualGland("Locus Coeruleus", ["Norepinephrine"], sensitivity=0.9),
            "thyroid": VirtualGland("Thyroid", ["T3", "T4"], sensitivity=0.3, fatigue_rate=0.001),
            "pineal": VirtualGland("Pineal", ["Melatonin"], sensitivity=0.5),
            "pancreas": VirtualGland("Pancreas", ["Insulin", "Glucagon"], sensitivity=0.6),
        }
        
    def tick(self, dt: float = 1.0):
        """
        Advance the endocrine system by one time step.
        
        1. Decay all hormone channels toward baseline
        2. Recover gland fatigue
        3. Process cascade effects
        4. Detect cognitive mode
        5. Notify subscribers
        """
        self.tick_count += 1
        
        # 1. Decay all channels
        for channel in self.channels.values():
            channel.decay(dt)
            
        # 2. Recover gland fatigue
        for gland in self.glands.values():
            gland.recover(dt)
            
        # 3. Process cascades (delayed effects from previous activations)
        self._process_cascades(dt)
        
        # 4. Detect cognitive mode
        old_mode = self.current_mode
        self._update_cognitive_mode()
        
        if self.current_mode == old_mode:
            self.mode_stability += dt
        else:
            self.mode_stability = 0.0
            self.mode_history.append((self.tick_count, self.current_mode))
            
        # 5. Notify subscribers
        state = self.get_state()
        for callback in self._subscribers:
            try:
                callback(state, self.current_mode)
            except Exception as e:
                logger.warning(f"Subscriber callback error: {e}")
                
    def signal_event(self, event_type: str, intensity: float = 1.0, source: str = "world"):
        """
        Signal an event to the endocrine system.
        Maps events to gland activations with appropriate intensities.
        """
        logger.info(f"Event: {event_type} (intensity={intensity:.2f}, source={source})")
        
        # Record event
        self.event_history.append({
            "tick": self.tick_count,
            "event": event_type,
            "intensity": intensity,
            "source": source
        })
        
        # Event → Gland mapping
        event_map = {
            "THREAT_DETECTED": [
                ("hypothalamus", 0.5),
                ("locus_coeruleus", 0.6),
                ("adrenal_medulla", 0.4),
            ],
            "THREAT_ESCAPED": [
                ("vta", 0.3),
                ("raphe_nuclei", 0.2),
            ],
            "REWARD_RECEIVED": [
                ("vta", 0.8),
                ("raphe_nuclei", 0.1),
            ],
            "SOCIAL_BOND": [
                ("hypothalamus", 0.7),  # Oxytocin release
            ],
            "COMBAT_HIT": [
                ("adrenal_medulla", 0.7),
                ("locus_coeruleus", 0.5),
                ("hypothalamus", 0.3),
            ],
            "COMBAT_VICTORY": [
                ("vta", 0.9),
                ("raphe_nuclei", 0.3),
            ],
            "MISSION_COMPLETE": [
                ("vta", 0.6),
                ("raphe_nuclei", 0.4),
            ],
            "EXPLORATION_DISCOVERY": [
                ("vta", 0.4),
                ("locus_coeruleus", 0.2),
            ],
            "FATIGUE_ACCUMULATION": [
                ("thyroid", -0.3),
                ("pineal", 0.4),
            ],
            "ENERGY_CONSUMED": [
                ("pancreas", 0.5),
                ("thyroid", 0.2),
            ],
            "DAMAGE_TAKEN": [
                ("adrenal_medulla", 0.6),
                ("hypothalamus", 0.4),
            ],
            "STEALTH_SUCCESS": [
                ("vta", 0.3),
                ("locus_coeruleus", -0.2),
            ],
        }
        
        activations = event_map.get(event_type, [])
        for gland_name, base_amount in activations:
            if gland_name in self.glands:
                gland = self.glands[gland_name]
                releases = gland.activate(abs(base_amount) * intensity)
                for hormone_name, amount in releases.items():
                    if hormone_name in self.channels:
                        if base_amount >= 0:
                            self.channels[hormone_name].release(amount)
                        else:
                            self.channels[hormone_name].suppress(amount)
                            
        # Trigger cascades
        self._trigger_cascades(activations, intensity)
        
    def _trigger_cascades(self, activations: List[Tuple[str, float]], intensity: float):
        """Trigger cascade effects from gland activations."""
        for gland_name, _ in activations:
            if gland_name in self._cascades:
                for target_gland, cascade_intensity, delay_factor in self._cascades[gland_name]:
                    if target_gland in self.glands:
                        # Immediate cascade (simplified from delayed)
                        releases = self.glands[target_gland].activate(cascade_intensity * intensity)
                        for hormone_name, amount in releases.items():
                            if hormone_name in self.channels:
                                self.channels[hormone_name].release(amount * delay_factor)
                                
    def _process_cascades(self, dt: float):
        """Process ongoing cascade effects (e.g., HPA axis feedback)."""
        # Negative feedback: High cortisol suppresses CRH
        if self.channels["Cortisol"].value > 0.5:
            suppression = (self.channels["Cortisol"].value - 0.5) * 0.1 * dt
            self.channels["CRH"].suppress(suppression)
            
        # Insulin-Glucagon balance
        if self.channels["Insulin"].value > 0.5:
            self.channels["Glucagon"].suppress(0.02 * dt)
        elif self.channels["Glucagon"].value > 0.4:
            self.channels["Insulin"].suppress(0.02 * dt)
            
        # Melatonin suppresses Norepinephrine (sleepiness reduces alertness)
        if self.channels["Melatonin"].value > 0.5:
            self.channels["Norepinephrine"].suppress(0.03 * dt)
            
    def _update_cognitive_mode(self):
        """
        Determine emergent cognitive mode from hormone space.
        Uses multi-dimensional centroid classification.
        """
        h = self.channels  # shorthand
        
        # Calculate mode scores
        scores = {
            CognitiveMode.STRESSED: (
                h["Cortisol"].value * 0.4 +
                h["Norepinephrine"].value * 0.3 +
                h["Epinephrine"].value * 0.2 +
                h["CRH"].value * 0.1
            ),
            CognitiveMode.REWARD: (
                h["Dopamine_Phasic"].value * 0.5 +
                h["Dopamine_Tonic"].value * 0.3 +
                h["Anandamide"].value * 0.2
            ),
            CognitiveMode.SOCIAL: (
                h["Oxytocin"].value * 0.6 +
                h["Serotonin"].value * 0.3 +
                h["Dopamine_Tonic"].value * 0.1
            ),
            CognitiveMode.FOCUSED: (
                h["Norepinephrine"].value * 0.4 +
                h["Dopamine_Tonic"].value * 0.3 +
                (1.0 - h["Melatonin"].value) * 0.2 +
                h["T3"].value * 0.1
            ),
            CognitiveMode.CREATIVE: (
                h["Dopamine_Tonic"].value * 0.3 +
                h["Serotonin"].value * 0.3 +
                h["Anandamide"].value * 0.2 +
                (1.0 - h["Cortisol"].value) * 0.2
            ),
            CognitiveMode.VIGILANT: (
                h["Norepinephrine"].value * 0.4 +
                h["Epinephrine"].value * 0.3 +
                h["CRH"].value * 0.2 +
                (1.0 - h["Melatonin"].value) * 0.1
            ),
            CognitiveMode.EXHAUSTED: (
                h["Melatonin"].value * 0.3 +
                (1.0 - h["T3"].value) * 0.2 +
                (1.0 - h["Norepinephrine"].value) * 0.2 +
                h["IL6"].value * 0.2 +
                (1.0 - h["Dopamine_Tonic"].value) * 0.1
            ),
            CognitiveMode.RESTING: 0.25  # Default baseline score
        }
        
        # Select highest-scoring mode
        best_mode = max(scores, key=scores.get)
        
        if best_mode != self.current_mode:
            old = self.current_mode
            self.current_mode = best_mode
            logger.info(f"Mode Transition: {old.value} → {best_mode.value} "
                       f"(score={scores[best_mode]:.3f}, stability={self.mode_stability:.1f})")
                       
    def subscribe(self, callback: Callable):
        """Register a callback to receive hormone state updates."""
        self._subscribers.append(callback)
        logger.info(f"Subscriber registered (total: {len(self._subscribers)})")
        
    def get_state(self) -> Dict[str, float]:
        """Return current hormone concentrations as a flat dict."""
        return {name: ch.value for name, ch in self.channels.items()}
        
    def get_full_state(self) -> Dict:
        """Return comprehensive system state including glands and mode."""
        return {
            "hormones": self.get_state(),
            "mode": self.current_mode.value,
            "mode_stability": self.mode_stability,
            "gland_fatigue": {name: g.fatigue for name, g in self.glands.items()},
            "tick": self.tick_count,
            "event_count": len(self.event_history),
        }
        
    def get_valence_arousal(self) -> Tuple[float, float]:
        """
        Map hormone state to valence-arousal space.
        Returns (valence, arousal) each in [-1, 1].
        """
        h = self.channels
        
        # Valence: positive emotions vs negative
        valence = (
            h["Dopamine_Tonic"].value * 0.3 +
            h["Serotonin"].value * 0.3 +
            h["Oxytocin"].value * 0.2 +
            h["Anandamide"].value * 0.2 -
            h["Cortisol"].value * 0.4 -
            h["IL6"].value * 0.2
        )
        valence = max(-1.0, min(1.0, valence * 2 - 0.5))
        
        # Arousal: activation level
        arousal = (
            h["Norepinephrine"].value * 0.3 +
            h["Epinephrine"].value * 0.3 +
            h["Dopamine_Phasic"].value * 0.2 +
            h["CRH"].value * 0.1 -
            h["Melatonin"].value * 0.3
        )
        arousal = max(-1.0, min(1.0, arousal * 2 - 0.3))
        
        return (valence, arousal)
        
    def reset(self):
        """Reset all channels to baseline."""
        for channel in self.channels.values():
            channel.value = channel.baseline
        for gland in self.glands.values():
            gland.fatigue = 0.0
        self.current_mode = CognitiveMode.RESTING
        self.mode_stability = 0.0
        self.event_history.clear()
        self.tick_count = 0
        logger.info("Endocrine system reset to baseline")


if __name__ == "__main__":
    logger.info("=== Virtual Endocrine System Demo (Full 16-Channel) ===")
    
    endo = VirtualEndocrineSystem()
    
    # Simulate a combat scenario
    logger.info("\n--- Combat Scenario ---")
    endo.signal_event("THREAT_DETECTED", 0.8, source="npc_enemy")
    endo.tick()
    v, a = endo.get_valence_arousal()
    logger.info(f"Valence={v:.2f}, Arousal={a:.2f}, Mode={endo.current_mode.value}")
    
    endo.signal_event("COMBAT_HIT", 0.6, source="gunfire")
    endo.tick()
    v, a = endo.get_valence_arousal()
    logger.info(f"Valence={v:.2f}, Arousal={a:.2f}, Mode={endo.current_mode.value}")
    
    endo.signal_event("COMBAT_VICTORY", 1.0, source="enemy_defeated")
    endo.tick()
    v, a = endo.get_valence_arousal()
    logger.info(f"Valence={v:.2f}, Arousal={a:.2f}, Mode={endo.current_mode.value}")
    
    # Let it decay
    logger.info("\n--- Recovery Phase ---")
    for i in range(10):
        endo.tick()
    v, a = endo.get_valence_arousal()
    logger.info(f"After 10 ticks: Valence={v:.2f}, Arousal={a:.2f}, Mode={endo.current_mode.value}")
    
    # Full state
    state = endo.get_full_state()
    logger.info(f"\nFull State: mode={state['mode']}, tick={state['tick']}, events={state['event_count']}")
    logger.info(f"Gland Fatigue: {state['gland_fatigue']}")
