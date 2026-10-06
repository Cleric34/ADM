"""
sim/agents.py - Agent Models for Chakravyuha Multi-Agent Simulation.

Defines Attacker (Abhimanyu, Followers, Scouts) and Defender units.
- Abhimanyu knows all 7 entry gate coordinates but NOT exit paths.
- Followers start with no gate knowledge and rely on visual scouting or messaging.
- Defenders scale in health and attack power as ring index decreases (inner rings are much stronger).
- Incorporates vision radius and distance-bounded message channels.
"""

from typing import Dict, List, Tuple, Optional, Any, Set
import math
import numpy as np


class Agent:
    """Base class for all tactical entities in the simulation."""

    def __init__(
        self,
        agent_id: str,
        side: str,
        pos: Tuple[int, int],
        health: int,
        attack_power: int,
        vision_radius: float = 4.0,
        comm_range: float = 6.0,
    ) -> None:
        self.agent_id = agent_id
        self.side = side  # 'pandava' or 'kaurava'
        self.pos = pos
        self.health = health
        self.max_health = health
        self.attack_power = attack_power
        self.vision_radius = vision_radius
        self.comm_range = comm_range
        self.is_alive = True

    def distance_to(self, other_pos: Tuple[int, int]) -> float:
        """Euclidean distance to another coordinate."""
        return math.hypot(self.pos[0] - other_pos[0], self.pos[1] - other_pos[1])

    def can_see(self, target_pos: Tuple[int, int]) -> bool:
        """Determines if target_pos is within agent's limited vision radius."""
        return self.distance_to(target_pos) <= self.vision_radius

    def can_communicate_with(self, other_agent: "Agent") -> bool:
        """Determines if other_agent is within radio/shout messaging range."""
        return self.distance_to(other_agent.pos) <= self.comm_range

    def take_damage(self, damage: int) -> None:
        """Applies damage and updates alive status."""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False


class Attacker(Agent):
    """
    Pandava warrior attacking the Chakravyuha.
    Roles:
      - 'infiltrator' (Abhimanyu): Knows all entry gates in advance, drives to center.
      - 'follower': Follows trail or communication signals.
      - 'scout': Dispatches to perimeter/intermediate rings to locate exit gates.
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        pos: Tuple[int, int],
        health: int = 220,
        attack_power: int = 40,
        vision_radius: float = 4.0,
        comm_range: float = 6.0,
        known_entry_gates: Optional[Dict[int, Tuple[int, int]]] = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            side="pandava",
            pos=pos,
            health=health,
            attack_power=attack_power,
            vision_radius=vision_radius,
            comm_range=comm_range,
        )
        self.role = role
        
        # Knowledge state under incomplete information
        self.known_entry_gates: Dict[int, Tuple[int, int]] = (
            dict(known_entry_gates) if known_entry_gates is not None else {}
        )
        self.known_exit_gates: Dict[int, Tuple[int, int]] = {}
        
        # Stateful waypoint targets
        self.target_entry_ring: int = 7
        self.target_exit_ring: int = 1
        self.current_target_ring: int = 7
        self.has_reached_center: bool = False
        self.has_exited: bool = False
        self.highest_ring_breached: int = 0
        
        # Communication inbox and outbox
        self.inbox: List[Dict[str, Any]] = []
        self.outbox: List[Dict[str, Any]] = []

    def receive_message(self, message: Dict[str, Any], sender: Agent) -> bool:
        """Accepts message if sender is within communication range."""
        if not self.is_alive:
            return False
        if self.can_communicate_with(sender):
            self.inbox.append(message)
            return True
        return False

    def process_inbox(self) -> None:
        """Integrates information received from other agents."""
        for msg in self.inbox:
            if "entry_gates" in msg:
                for ring, gate_pos in msg["entry_gates"].items():
                    if ring not in self.known_entry_gates:
                        self.known_entry_gates[ring] = gate_pos
            if "exit_gates" in msg:
                for ring, gate_pos in msg["exit_gates"].items():
                    if ring not in self.known_exit_gates:
                        self.known_exit_gates[ring] = gate_pos
        self.inbox.clear()

    def scout_vision(self, env: Any) -> None:
        """Inspects cells within vision radius and records any spotted gates."""
        if not self.is_alive:
            return
            
        for r, gate_pos in env.entry_gates.items():
            if self.can_see(gate_pos):
                self.known_entry_gates[r] = gate_pos
                
        for r, gate_pos in env.exit_gates.items():
            if self.can_see(gate_pos):
                self.known_exit_gates[r] = gate_pos


class Defender(Agent):
    """
    Kaurava warrior defending a specific concentric ring of the formation.
    Inner ring defenders (Ring 1, Drona's core) have higher health and attack power.
    """

    def __init__(
        self,
        agent_id: str,
        layer: int,
        pos: Tuple[int, int],
        vision_radius: float = 3.0,
        comm_range: float = 5.0,
    ) -> None:
        self.layer = layer  # 1 (innermost) to 7 (outermost)
        
        # Power scaling: Inner rings house veteran Maharathis
        # Layer 7: HP 19, ATK 8 | Layer 1: HP 43, ATK 20
        power_scale = 8 - layer  # 1 for layer 7, 7 for layer 1
        health = 15 + power_scale * 4
        attack = 6 + power_scale * 2
        
        super().__init__(
            agent_id=agent_id,
            side="kaurava",
            pos=pos,
            health=health,
            attack_power=attack,
            vision_radius=vision_radius,
            comm_range=comm_range,
        )
        
        colors = {
            1: "#9B2C2C",
            2: "#C53030",
            3: "#E53E3E",
            4: "#F56565",
            5: "#FC8181",
            6: "#FEB2B2",
            7: "#FED7D7",
        }
        self.strength_color = colors.get(layer, "#E53E3E")
