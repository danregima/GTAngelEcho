"""
GTAngel - World Navigation & Mission Intelligence
Autonomous NPC navigation, pathfinding, and mission planning in open-world environments.
"""
import logging
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("GTAngel.Navigation")


class MissionType(Enum):
    PATROL = "patrol"
    DELIVERY = "delivery"
    COMBAT = "combat"
    STEALTH = "stealth"
    SOCIAL = "social"
    EXPLORATION = "exploration"


@dataclass
class Waypoint:
    """A navigation waypoint in the game world."""
    x: float
    y: float
    z: float = 0.0
    name: str = ""
    danger_level: float = 0.0
    
    def distance_to(self, other: 'Waypoint') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class Mission:
    """A mission or objective for the GTAngel agent."""
    id: str
    mission_type: MissionType
    waypoints: List[Waypoint]
    priority: float = 0.5
    time_limit: Optional[float] = None
    reward: float = 100.0
    completed: bool = False


class WorldMap:
    """
    Simplified world representation for navigation.
    In a full implementation, this would interface with UE5 NavMesh.
    """
    
    def __init__(self):
        self.landmarks: Dict[str, Waypoint] = {
            "downtown": Waypoint(0, 0, 0, "Downtown", 0.3),
            "harbor": Waypoint(100, -50, 0, "Harbor", 0.5),
            "hills": Waypoint(-80, 120, 50, "Vinewood Hills", 0.1),
            "airport": Waypoint(150, 100, 0, "Airport", 0.4),
            "beach": Waypoint(-100, -80, 0, "Beach", 0.2),
            "industrial": Waypoint(80, 80, 0, "Industrial Zone", 0.7),
            "suburbs": Waypoint(-50, 60, 0, "Suburbs", 0.1),
            "nightclub": Waypoint(20, -30, 0, "Nightclub District", 0.4),
        }
        self.danger_zones: List[Tuple[Waypoint, float]] = []  # (center, radius)
        logger.info(f"World Map loaded: {len(self.landmarks)} landmarks")
        
    def get_safe_path(self, start: Waypoint, end: Waypoint) -> List[Waypoint]:
        """Find a path avoiding high-danger areas (simplified A*)."""
        # Simplified: direct path with intermediate waypoints
        path = [start]
        
        # Add intermediate points if distance is large
        dist = start.distance_to(end)
        if dist > 50:
            mid = Waypoint(
                (start.x + end.x) / 2 + random.uniform(-10, 10),
                (start.y + end.y) / 2 + random.uniform(-10, 10),
                (start.z + end.z) / 2
            )
            path.append(mid)
            
        path.append(end)
        return path


class GTAngelNavigator:
    """
    GTAngel Navigation Intelligence.
    Combines pathfinding with cognitive decision-making for autonomous NPC behavior.
    """
    
    def __init__(self):
        self.world = WorldMap()
        self.position = Waypoint(0, 0, 0, "Start")
        self.current_mission: Optional[Mission] = None
        self.mission_queue: List[Mission] = []
        self.path: List[Waypoint] = []
        self.path_index: int = 0
        self.speed: float = 5.0  # units per tick
        self.awareness_radius: float = 30.0
        logger.info("GTAngel Navigator initialized")
        
    def assign_mission(self, mission: Mission):
        """Assign a new mission to the navigator."""
        self.mission_queue.append(mission)
        self.mission_queue.sort(key=lambda m: m.priority, reverse=True)
        logger.info(f"Mission assigned: {mission.id} ({mission.mission_type.value})")
        
    def start_next_mission(self):
        """Start the highest-priority mission from the queue."""
        if not self.mission_queue:
            logger.info("No missions in queue. Entering patrol mode.")
            self._generate_patrol_mission()
            return
            
        self.current_mission = self.mission_queue.pop(0)
        if self.current_mission.waypoints:
            target = self.current_mission.waypoints[0]
            self.path = self.world.get_safe_path(self.position, target)
            self.path_index = 0
            logger.info(f"Starting mission: {self.current_mission.id} → {target.name}")
            
    def tick(self) -> Dict:
        """Advance navigation by one tick."""
        if not self.current_mission:
            self.start_next_mission()
            
        if self.path and self.path_index < len(self.path):
            target = self.path[self.path_index]
            dist = self.position.distance_to(target)
            
            if dist <= self.speed:
                # Reached waypoint
                self.position = target
                self.path_index += 1
                logger.info(f"Reached waypoint: ({target.x:.1f}, {target.y:.1f})")
                
                # Check if mission complete
                if self.path_index >= len(self.path):
                    if self.current_mission:
                        self.current_mission.completed = True
                        logger.info(f"Mission complete: {self.current_mission.id}")
                        self.current_mission = None
            else:
                # Move toward target
                dx = target.x - self.position.x
                dy = target.y - self.position.y
                norm = math.sqrt(dx**2 + dy**2)
                self.position = Waypoint(
                    self.position.x + (dx / norm) * self.speed,
                    self.position.y + (dy / norm) * self.speed
                )
                
        return {
            "position": (self.position.x, self.position.y, self.position.z),
            "mission": self.current_mission.id if self.current_mission else "none",
            "path_progress": f"{self.path_index}/{len(self.path)}"
        }
        
    def _generate_patrol_mission(self):
        """Generate a random patrol mission."""
        landmarks = list(self.world.landmarks.values())
        target = random.choice(landmarks)
        mission = Mission(
            id=f"patrol_{random.randint(1000, 9999)}",
            mission_type=MissionType.PATROL,
            waypoints=[target],
            priority=0.1
        )
        self.assign_mission(mission)
        
    def scan_environment(self) -> Dict:
        """Scan nearby environment for threats and opportunities."""
        nearby = {}
        for name, wp in self.world.landmarks.items():
            dist = self.position.distance_to(wp)
            if dist <= self.awareness_radius:
                nearby[name] = {"distance": dist, "danger": wp.danger_level}
        return nearby


if __name__ == "__main__":
    logger.info("=== GTAngel Navigation Demo ===")
    
    nav = GTAngelNavigator()
    
    # Assign a delivery mission
    mission = Mission(
        id="delivery_001",
        mission_type=MissionType.DELIVERY,
        waypoints=[nav.world.landmarks["harbor"]],
        priority=0.8,
        reward=500.0
    )
    nav.assign_mission(mission)
    
    # Run simulation
    for i in range(20):
        state = nav.tick()
        if i % 5 == 0:
            logger.info(f"Tick {i}: {state}")
            
    # Scan environment
    nearby = nav.scan_environment()
    logger.info(f"Nearby landmarks: {nearby}")
