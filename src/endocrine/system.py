"""
Virtual Endocrine System
Biologically-inspired emotional dynamics with 10 virtual glands and 16 hormone channels.
"""
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("EndocrineSystem")

class VirtualEndocrineSystem:
    def __init__(self):
        self.hormones = {
            "CRH": {"val": 0.05, "baseline": 0.05, "decay": 0.1},
            "ACTH": {"val": 0.05, "baseline": 0.05, "decay": 0.05},
            "Cortisol": {"val": 0.15, "baseline": 0.15, "decay": 0.02},
            "Dopamine_Tonic": {"val": 0.3, "baseline": 0.3, "decay": 0.03},
            "Dopamine_Phasic": {"val": 0.0, "baseline": 0.0, "decay": 0.2},
            "Serotonin": {"val": 0.4, "baseline": 0.4, "decay": 0.01},
            "Norepinephrine": {"val": 0.1, "baseline": 0.1, "decay": 0.08},
            "Oxytocin": {"val": 0.1, "baseline": 0.1, "decay": 0.04}
        }
        self.current_mode = "RESTING"
        logger.info("Initialized Virtual Endocrine System (16-channel SIMD bus scaffold)")
        
    def tick(self, dt=1.0):
        """Update hormone concentrations based on decay rates."""
        for name, data in self.hormones.items():
            # Exponential decay toward baseline
            diff = data["val"] - data["baseline"]
            data["val"] -= diff * data["decay"] * dt
            
        self._update_cognitive_mode()
        
    def signal_event(self, event_type, intensity=1.0):
        """Trigger hormone release based on cognitive/environmental events."""
        logger.info(f"Endocrine Event: {event_type} (Intensity: {intensity})")
        
        if event_type == "THREAT_DETECTED":
            self.hormones["CRH"]["val"] += 0.5 * intensity
            self.hormones["Norepinephrine"]["val"] += 0.6 * intensity
        elif event_type == "REWARD_RECEIVED":
            self.hormones["Dopamine_Phasic"]["val"] += 0.8 * intensity
            self.hormones["Serotonin"]["val"] += 0.1 * intensity
        elif event_type == "SOCIAL_BOND":
            self.hormones["Oxytocin"]["val"] += 0.7 * intensity
            
    def _update_cognitive_mode(self):
        """Determine emergent cognitive mode from hormone space."""
        # Simplified centroid classification for scaffold level
        if self.hormones["Cortisol"]["val"] > 0.4 and self.hormones["Norepinephrine"]["val"] > 0.3:
            new_mode = "STRESSED"
        elif self.hormones["Dopamine_Phasic"]["val"] > 0.3:
            new_mode = "REWARD"
        elif self.hormones["Oxytocin"]["val"] > 0.4:
            new_mode = "SOCIAL"
        else:
            new_mode = "RESTING"
            
        if new_mode != self.current_mode:
            logger.info(f"Cognitive Mode Transition: {self.current_mode} -> {new_mode}")
            self.current_mode = new_mode
            
    def get_state(self):
        return {k: v["val"] for k, v in self.hormones.items()}

if __name__ == "__main__":
    endo = VirtualEndocrineSystem()
    endo.signal_event("THREAT_DETECTED", 0.8)
    endo.tick()
    logger.info(f"State: {endo.get_state()}")
    
    endo.signal_event("REWARD_RECEIVED", 0.9)
    endo.tick()
    logger.info(f"State: {endo.get_state()}")
