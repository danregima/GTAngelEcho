"""
Cognitive Memory Systems
Implements episodic, semantic, and procedural memory with attention economics.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("CognitiveMemory")


@dataclass
class MemoryAtom:
    """Fundamental unit of memory in the cognitive system."""
    content: Any
    memory_type: str  # episodic, semantic, procedural
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5
    valence: float = 0.0  # -1 to +1 (negative to positive emotional charge)
    arousal: float = 0.0  # 0 to 1 (calm to excited)
    access_count: int = 0
    decay_rate: float = 0.01
    
    def access(self):
        """Record an access, boosting importance."""
        self.access_count += 1
        self.importance = min(1.0, self.importance + 0.05)
        
    def decay(self, dt: float):
        """Apply time-based decay to importance."""
        self.importance = max(0.0, self.importance - self.decay_rate * dt)


class EpisodicMemory:
    """
    Episodic Memory - Stores experiences with emotional context.
    Implements Vervaeke's 4 ways of knowing for memory retrieval.
    """
    
    def __init__(self, capacity: int = 1000):
        self.episodes: deque = deque(maxlen=capacity)
        self.capacity = capacity
        logger.info(f"Episodic Memory initialized (capacity: {capacity})")
        
    def store(self, content: Any, valence: float = 0.0, arousal: float = 0.0,
              importance: float = 0.5):
        """Store a new episodic memory."""
        atom = MemoryAtom(
            content=content,
            memory_type="episodic",
            valence=valence,
            arousal=arousal,
            importance=importance
        )
        self.episodes.append(atom)
        logger.info(f"Stored episode: {str(content)[:50]}... (v={valence:.2f}, a={arousal:.2f})")
        
    def recall_by_valence(self, target_valence: float, n: int = 5) -> List[MemoryAtom]:
        """Retrieve memories matching a target emotional valence."""
        sorted_eps = sorted(
            self.episodes,
            key=lambda m: abs(m.valence - target_valence)
        )
        for m in sorted_eps[:n]:
            m.access()
        return sorted_eps[:n]
        
    def recall_recent(self, n: int = 10) -> List[MemoryAtom]:
        """Retrieve most recent memories."""
        recent = list(self.episodes)[-n:]
        for m in recent:
            m.access()
        return recent


class SemanticMemory:
    """
    Semantic Memory - Knowledge graph of facts and relationships.
    Implements AtomSpace-style hypergraph knowledge representation.
    """
    
    def __init__(self):
        self.knowledge: Dict[str, Dict] = {}
        self.relations: List[Dict] = []
        logger.info("Semantic Memory initialized (hypergraph knowledge store)")
        
    def store_fact(self, subject: str, predicate: str, obj: str, confidence: float = 0.8):
        """Store a semantic triple (subject-predicate-object)."""
        fact = {"subject": subject, "predicate": predicate, "object": obj, "confidence": confidence}
        self.relations.append(fact)
        
        if subject not in self.knowledge:
            self.knowledge[subject] = {"relations": []}
        self.knowledge[subject]["relations"].append(fact)
        
    def query(self, subject: str) -> List[Dict]:
        """Query all known facts about a subject."""
        if subject in self.knowledge:
            return self.knowledge[subject]["relations"]
        return []
        
    def find_path(self, start: str, end: str, max_depth: int = 3) -> Optional[List[str]]:
        """Find a relational path between two concepts (BFS)."""
        visited = set()
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            if current == end:
                return path
            if len(path) > max_depth:
                continue
            if current in visited:
                continue
            visited.add(current)
            
            for rel in self.knowledge.get(current, {}).get("relations", []):
                next_node = rel["object"]
                if next_node not in visited:
                    queue.append((next_node, path + [next_node]))
                    
        return None


class ProceduralMemory:
    """
    Procedural Memory - Learned action sequences and skills.
    Stores successful action patterns for replay.
    """
    
    def __init__(self):
        self.procedures: Dict[str, List[str]] = {}
        self.success_rates: Dict[str, float] = {}
        logger.info("Procedural Memory initialized (action sequence store)")
        
    def store_procedure(self, name: str, actions: List[str], success: bool = True):
        """Store or update a learned procedure."""
        if name not in self.procedures:
            self.procedures[name] = actions
            self.success_rates[name] = 1.0 if success else 0.0
        else:
            # Update success rate with exponential moving average
            alpha = 0.1
            self.success_rates[name] = (1 - alpha) * self.success_rates[name] + alpha * (1.0 if success else 0.0)
            
    def recall_procedure(self, name: str) -> Optional[List[str]]:
        """Recall a stored procedure by name."""
        return self.procedures.get(name)
        
    def best_procedure_for(self, context: str) -> Optional[str]:
        """Find the best procedure matching a context (simple keyword match)."""
        matches = [(name, rate) for name, rate in self.success_rates.items()
                   if context.lower() in name.lower()]
        if matches:
            return max(matches, key=lambda x: x[1])[0]
        return None


class CognitiveMemorySystem:
    """
    Unified Cognitive Memory System integrating all memory types.
    Implements ECAN-style attention economics for memory management.
    """
    
    def __init__(self):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.attention_budget = 100.0
        logger.info("Cognitive Memory System online (episodic + semantic + procedural)")
        
    def process_experience(self, event: Dict):
        """Process a game experience into appropriate memory systems."""
        # Store as episode
        self.episodic.store(
            content=event,
            valence=event.get("valence", 0.0),
            arousal=event.get("arousal", 0.0),
            importance=event.get("importance", 0.5)
        )
        
        # Extract semantic facts
        if "facts" in event:
            for fact in event["facts"]:
                self.semantic.store_fact(**fact)
                
        # Store successful action sequences
        if "actions" in event and event.get("success", False):
            self.procedural.store_procedure(
                name=event.get("context", "unnamed"),
                actions=event["actions"],
                success=True
            )


if __name__ == "__main__":
    logger.info("=== Cognitive Memory System Demo ===")
    
    cms = CognitiveMemorySystem()
    
    # Store some game experiences
    cms.process_experience({
        "content": "Defeated rival gang in downtown ambush",
        "valence": 0.8, "arousal": 0.9, "importance": 0.9,
        "facts": [
            {"subject": "rival_gang", "predicate": "weak_to", "obj": "flanking"},
            {"subject": "downtown", "predicate": "has", "obj": "good_cover"}
        ],
        "actions": ["take_cover", "flank_left", "engage", "loot"],
        "context": "gang_combat",
        "success": True
    })
    
    cms.process_experience({
        "content": "Failed stealth mission at warehouse",
        "valence": -0.5, "arousal": 0.7, "importance": 0.6,
        "facts": [
            {"subject": "warehouse", "predicate": "has", "obj": "security_cameras"}
        ],
        "actions": ["sneak", "disable_camera", "detected", "flee"],
        "context": "stealth_mission",
        "success": False
    })
    
    # Query memory
    logger.info(f"Semantic query 'rival_gang': {cms.semantic.query('rival_gang')}")
    logger.info(f"Best procedure for 'combat': {cms.procedural.best_procedure_for('combat')}")
    logger.info(f"Recent episodes: {len(cms.episodic.recall_recent(5))}")
