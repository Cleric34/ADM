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
        health: int = 100,
        attack_power: int = 30,
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
        # Abhimanyu knows all entry gates, but NOT exit gates.
        self.known_entry_gates: Dict[int, Tuple[int, int]] = (
            dict(known_entry_gates) if known_entry_gates is not None else {}
        )
        self.known_exit_gates: Dict[int, Tuple[int, int]] = {}
        
        # Mission progression state
        self.current_target_ring = 7  # Start by targeting Ring 7 entry, down to 1 then center (0)
        self.has_reached_center = False
        self.has_exited = False
        self.highest_ring_breached = 0  # 0: none, 7: outer, 1: innermost, 0: center
        
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
            # Update known entry gates
            if "entry_gates" in msg:
                for ring, gate_pos in msg["entry_gates"].items():
                    if ring not in self.known_entry_gates:
                        self.known_entry_gates[ring] = gate_pos
            # Update known exit gates
            if "exit_gates" in msg:
                for ring, gate_pos in msg["exit_gates"].items():
                    if ring not in self.known_exit_gates:
                        self.known_exit_gates[ring] = gate_pos
        self.inbox.clear()

    def scout_vision(self, env: Any) -> None:
        """Inspects cells within vision radius and records any spotted gates."""
        if not self.is_alive:
            return
            
        # Check all ring gates in environment to see if within vision radius
        for r, gate_pos in env.entry_gates.items():
            if self.can_see(gate_pos):
                self.known_entry_gates[r] = gate_pos
                
        for r, gate_pos in env.exit_gates.items():
            if self.can_see(gate_pos):
                self.known_exit_gates[r] = gate_pos


class Defender(Agent):
    """
    Kaurava warrior defending a specific concentric ring of the formation.
    Inner ring defenders (Ring 1, Drona's core) have significantly higher health and attack power.
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
        
        # Power scaling: Inner rings are veteran Maharathis (Drona, Karna, Ashwatthama)
        # Ring 7: HP 35, ATK 12 | Ring 1: HP 95, ATK 36
        power_scale = 8 - layer  # 1 for layer 7, 7 for layer 1
        health = 25 + power_scale * 10
        attack = 10 + power_scale * 4
        
        super().__init__(
            agent_id=agent_id,
            side="kaurava",
            pos=pos,
            health=health,
            attack_power=attack,
            vision_radius=vision_radius,
            comm_range=comm_range,
        )
        
        # Color mapping for visualization: darker/richer red for stronger inner guards
        colors = {
            1: "#9B2C2C",  # Deep Crimson (Maharathi)
            2: "#C53030",
            3: "#E53E3E",
            4: "#F56565",
            5: "#FC8181",
            6: "#FEB2B2",
            7: "#FED7D7",  # Light Pink (Outer perimeter guard)
        }
        self.strength_color = colors.get(layer, "#E53E3E")
