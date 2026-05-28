"""
SuperHotGirl — Avatar Expression System
Implements MetaHuman DNA FACS mapping, Lorenz attractor chaotic micro-expressions,
and aesthetic bias parameters for the GTAngelEcho avatar.

KSM Cycle 1: Strengthened Deep Interlock with Endocrine (full hormone mapping),
added get_expression_state() for integration hub, and expanded FACS coverage.
"""
import math
import random
import logging
from typing import Dict, List
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("SuperHotGirl")


@dataclass
class LorenzState:
    """Lorenz attractor state for chaotic micro-expressions."""
    x: float = 1.0
    y: float = 1.0
    z: float = 1.0
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    dt: float = 0.005
    
    def step(self):
        """Advance Lorenz attractor by one step."""
        dx = self.sigma * (self.y - self.x) * self.dt
        dy = (self.x * (self.rho - self.z) - self.y) * self.dt
        dz = (self.x * self.y - self.beta * self.z) * self.dt
        self.x += dx
        self.y += dy
        self.z += dz
        
    def get_perturbation(self, scale: float = 0.01) -> float:
        """Get a bounded perturbation from the attractor."""
        self.step()
        # Normalize to [-1, 1] range (Lorenz x typically in [-20, 20])
        return max(-1.0, min(1.0, self.x / 20.0)) * scale


class AvatarExpressionSystem:
    """
    SuperHotGirl Avatar Expression System.
    
    Maps endocrine state to FACS Action Units with:
    - Full hormone-to-AU mapping (Cortisol, Dopamine, Oxytocin, Norepinephrine, Serotonin)
    - Lorenz attractor chaotic micro-expressions (not random noise)
    - 5 aesthetic bias parameters
    - Expression state export for rendering pipeline
    """
    
    def __init__(self, chaos_intensity: float = 0.15):
        self.chaos_intensity = chaos_intensity
        
        # Aesthetic parameters (SuperHotGirl signature)
        self.aesthetic_params = {
            "ConfidencePosture": 0.8,
            "Charisma": 0.7,
            "EyeSparkle": 0.9,
            "GracefulMovement": 0.8,
            "EmissiveGlow": 0.5
        }
        
        # FACS Action Units (18 core AUs)
        self.action_units: Dict[str, float] = {
            "AU1": 0.0,   # Inner Brow Raise
            "AU2": 0.0,   # Outer Brow Raise
            "AU4": 0.0,   # Brow Lowerer
            "AU5": 0.0,   # Upper Lid Raise
            "AU6": 0.0,   # Cheek Raise
            "AU7": 0.0,   # Lid Tightener
            "AU9": 0.0,   # Nose Wrinkle
            "AU10": 0.0,  # Upper Lip Raise
            "AU12": 0.0,  # Lip Corner Puller (Smile)
            "AU14": 0.0,  # Dimpler
            "AU15": 0.0,  # Lip Corner Depressor (Frown)
            "AU17": 0.0,  # Chin Raise
            "AU20": 0.0,  # Lip Stretch
            "AU23": 0.0,  # Lip Tightener
            "AU24": 0.0,  # Lip Pressor
            "AU25": 0.0,  # Lips Part
            "AU26": 0.0,  # Jaw Drop
            "AU27": 0.0,  # Mouth Stretch
        }
        
        # Lorenz attractor for each AU group (3 attractors for variety)
        self._lorenz_upper = LorenzState(x=1.0, y=1.0, z=1.0)
        self._lorenz_mid = LorenzState(x=0.5, y=0.8, z=1.2)
        self._lorenz_lower = LorenzState(x=1.5, y=0.3, z=0.9)
        
        # Expression blend weights (for smooth transitions)
        self._target_aus: Dict[str, float] = dict(self.action_units)
        self._blend_rate: float = 0.3  # How fast AUs approach targets
        
        logger.info("SuperHotGirl Expression System initialized (18 AUs, Lorenz chaos, 5 aesthetics)")
        
    def update_from_endocrine(self, hormone_state: Dict[str, float]):
        """
        Map hormone concentrations to FACS Action Units.
        
        Mapping:
        - Cortisol → AU4 (Brow Lowerer), AU1 (Inner Brow Raise), AU23 (Lip Tightener)
        - Dopamine_Phasic → AU12 (Smile), AU6 (Cheek Raise), AU25 (Lips Part)
        - Oxytocin → AU6 (Cheek Raise), AU12 (Smile), AU14 (Dimpler)
        - Norepinephrine → AU5 (Upper Lid Raise), AU7 (Lid Tightener), AU20 (Lip Stretch)
        - Serotonin → AU12 (subtle smile), reduces AU4 (brow tension)
        """
        # Cortisol → Stress expression
        cortisol = hormone_state.get("cortisol", hormone_state.get("Cortisol", 0.0))
        if cortisol > 0.1:
            self._target_aus["AU4"] = min(1.0, cortisol * 1.5)
            self._target_aus["AU1"] = min(1.0, cortisol * 0.8)
            self._target_aus["AU23"] = min(1.0, cortisol * 0.6)
            
        # Dopamine → Reward/Joy expression
        dopamine = hormone_state.get("dopamine_phasic", hormone_state.get("Dopamine_Phasic", 0.0))
        if dopamine > 0.05:
            self._target_aus["AU12"] = min(1.0, dopamine * 2.0)
            self._target_aus["AU6"] = min(1.0, dopamine * 1.5)
            self._target_aus["AU25"] = min(1.0, dopamine * 1.0)
            
        # Oxytocin → Warm/Social expression
        oxytocin = hormone_state.get("oxytocin", hormone_state.get("Oxytocin", 0.0))
        if oxytocin > 0.1:
            self._target_aus["AU6"] = min(1.0, self._target_aus["AU6"] + oxytocin * 0.8)
            self._target_aus["AU12"] = min(1.0, self._target_aus["AU12"] + oxytocin * 0.5)
            self._target_aus["AU14"] = min(1.0, oxytocin * 0.7)
            
        # Norepinephrine → Alert/Wide-eyed expression
        norepinephrine = hormone_state.get("norepinephrine", hormone_state.get("Norepinephrine", 0.0))
        if norepinephrine > 0.1:
            self._target_aus["AU5"] = min(1.0, norepinephrine * 1.8)
            self._target_aus["AU7"] = min(1.0, norepinephrine * 1.0)
            self._target_aus["AU20"] = min(1.0, norepinephrine * 0.5)
            
        # Serotonin → Calm contentment (subtle smile, relaxed brow)
        serotonin = hormone_state.get("serotonin", hormone_state.get("Serotonin", 0.0))
        if serotonin > 0.3:
            self._target_aus["AU12"] = max(self._target_aus["AU12"], serotonin * 0.4)
            self._target_aus["AU4"] = max(0.0, self._target_aus["AU4"] - serotonin * 0.3)
            
        # Blend current AUs toward targets
        for au in self.action_units:
            diff = self._target_aus[au] - self.action_units[au]
            self.action_units[au] += diff * self._blend_rate
            
    def apply_chaotic_micro_expressions(self):
        """
        Apply Lorenz attractor perturbations for natural micro-movements.
        Uses 3 separate attractors for upper face, mid face, and lower face.
        """
        upper_face = ["AU1", "AU2", "AU4", "AU5"]
        mid_face = ["AU6", "AU7", "AU9", "AU10"]
        lower_face = ["AU12", "AU14", "AU15", "AU17", "AU20", "AU23", "AU24", "AU25", "AU26", "AU27"]
        
        for au in upper_face:
            perturbation = self._lorenz_upper.get_perturbation(self.chaos_intensity)
            self.action_units[au] = max(0.0, min(1.0, self.action_units[au] + perturbation))
            
        for au in mid_face:
            perturbation = self._lorenz_mid.get_perturbation(self.chaos_intensity * 0.7)
            self.action_units[au] = max(0.0, min(1.0, self.action_units[au] + perturbation))
            
        for au in lower_face:
            perturbation = self._lorenz_lower.get_perturbation(self.chaos_intensity * 0.5)
            self.action_units[au] = max(0.0, min(1.0, self.action_units[au] + perturbation))
            
    def apply_aesthetic_bias(self):
        """
        Apply SuperHotGirl aesthetic parameters to bias expressions.
        
        - ConfidencePosture: Subtle smile baseline, reduced frown
        - Charisma: Enhanced cheek raise and eye engagement
        - EyeSparkle: Upper lid raise, lid tightener
        - GracefulMovement: Smoother transitions (reduced chaos)
        - EmissiveGlow: Affects rendering, not AUs directly
        """
        conf = self.aesthetic_params["ConfidencePosture"]
        char = self.aesthetic_params["Charisma"]
        spark = self.aesthetic_params["EyeSparkle"]
        grace = self.aesthetic_params["GracefulMovement"]
        
        # Confidence → baseline smile, suppress frown
        self.action_units["AU12"] = max(self.action_units["AU12"], conf * 0.3)
        self.action_units["AU15"] *= (1.0 - conf * 0.5)
        
        # Charisma → enhanced cheek raise and engagement
        self.action_units["AU6"] = max(self.action_units["AU6"], char * 0.2)
        self.action_units["AU14"] = max(self.action_units["AU14"], char * 0.15)
        
        # Eye Sparkle → upper lid and tightener
        self.action_units["AU5"] = max(self.action_units["AU5"], spark * 0.25)
        self.action_units["AU7"] = max(self.action_units["AU7"], spark * 0.1)
        
        # Graceful Movement → reduce chaos intensity dynamically
        # (Higher grace = less chaotic perturbation)
        self.chaos_intensity = 0.15 * (1.0 - grace * 0.5)
        
    def get_expression_state(self) -> Dict:
        """
        Export the full expression state for the rendering pipeline.
        
        Returns:
            Dict with action_units, aesthetics, and derived metrics.
        """
        # Calculate expression intensity (overall facial activation)
        total_activation = sum(self.action_units.values())
        max_possible = len(self.action_units)
        intensity = total_activation / max_possible if max_possible > 0 else 0.0
        
        # Determine dominant expression
        expression_profiles = {
            "joy": (self.action_units["AU6"] + self.action_units["AU12"]) / 2,
            "anger": (self.action_units["AU4"] + self.action_units["AU23"] + self.action_units["AU24"]) / 3,
            "surprise": (self.action_units["AU1"] + self.action_units["AU2"] + self.action_units["AU5"] + self.action_units["AU26"]) / 4,
            "fear": (self.action_units["AU1"] + self.action_units["AU4"] + self.action_units["AU5"] + self.action_units["AU20"]) / 4,
            "disgust": (self.action_units["AU9"] + self.action_units["AU10"] + self.action_units["AU17"]) / 3,
            "sadness": (self.action_units["AU1"] + self.action_units["AU15"] + self.action_units["AU17"]) / 3,
            "neutral": max(0.0, 1.0 - intensity * 2),
        }
        dominant = max(expression_profiles, key=expression_profiles.get)
        
        return {
            "action_units": dict(self.action_units),
            "aesthetics": dict(self.aesthetic_params),
            "intensity": intensity,
            "dominant_expression": dominant,
            "expression_scores": expression_profiles,
            "chaos_intensity": self.chaos_intensity,
        }
        
    def reset(self):
        """Reset all action units to zero."""
        for au in self.action_units:
            self.action_units[au] = 0.0
            self._target_aus[au] = 0.0


if __name__ == "__main__":
    logger.info("=== SuperHotGirl Expression Demo ===")
    
    aes = AvatarExpressionSystem()
    
    # Simulate high-dopamine reward state
    logger.info("\n--- Reward State ---")
    aes.update_from_endocrine({"cortisol": 0.1, "dopamine_phasic": 0.8, "oxytocin": 0.3, "serotonin": 0.5})
    aes.apply_chaotic_micro_expressions()
    aes.apply_aesthetic_bias()
    state = aes.get_expression_state()
    logger.info(f"Dominant: {state['dominant_expression']} (intensity={state['intensity']:.3f})")
    logger.info(f"Joy score: {state['expression_scores']['joy']:.3f}")
    
    # Simulate stressed state
    logger.info("\n--- Stressed State ---")
    aes.reset()
    aes.update_from_endocrine({"cortisol": 0.7, "norepinephrine": 0.6, "dopamine_phasic": 0.0})
    aes.apply_chaotic_micro_expressions()
    aes.apply_aesthetic_bias()
    state = aes.get_expression_state()
    logger.info(f"Dominant: {state['dominant_expression']} (intensity={state['intensity']:.3f})")
    logger.info(f"Anger score: {state['expression_scores']['anger']:.3f}")
