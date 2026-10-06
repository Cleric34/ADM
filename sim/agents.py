"""
Agents Module for Chakravyuha Simulation.

Defines base and specialized warrior agents (Infiltrator e.g., Abhimanyu, Defenders e.g., Kaurava Commanders,
and Formation Soldiers) with localized state, perception under incomplete information, stamina, and health.
"""

from typing import Any, Dict, Optional


class BaseAgent:
    """Base class for all tactical agents participating in the Chakravyuha simulation."""

    def __init__(self, agent_id: str, side: str, role: str) -> None:
        self.agent_id = agent_id
        self.side = side  # 'pandava' or 'kaurava'
        self.role = role
        self.is_alive = True

    def observe(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate localized perception of the environment under incomplete information."""
        return {}

    def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Decide an action given current partial observation."""
        return {}


class InfiltratorAgent(BaseAgent):
    """Represents an entrant attempting penetration and strategic navigation through formation tiers."""

    def __init__(self, agent_id: str = "abhimanyu") -> None:
        super().__init__(agent_id=agent_id, side="pandava", role="infiltrator")


class DefenderAgent(BaseAgent):
    """Represents formation guardians / commanders maintaining ring integrity and coordinated trapping."""

    def __init__(self, agent_id: str, layer: int, role: str = "defender") -> None:
        super().__init__(agent_id=agent_id, side="kaurava", role=role)
        self.layer = layer
