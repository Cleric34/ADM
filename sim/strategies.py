"""
sim/strategies.py - Attacker Multi-Agent Coordination Strategies.

Implements the four tactical strategies under incomplete information:
1. `lone_entry`: Abhimanyu enters the formation completely alone.
2. `blind_follow`: Followers trail Abhimanyu's position with zero communication.
3. `shared_map`: Agents continuously broadcast discovered entry and exit gates over the message channel.
4. `split_exit`: A designated scout subgroup explores outer rings to find exit routes while the strike force penetrates inwards.
"""

from typing import List, Dict, Tuple, Optional, Any, Set
import numpy as np
from sim.agents import Attacker, Defender, Agent
from sim.environment import ChakravyuhaEnvironment, Config


def get_next_step_towards(
    current_pos: Tuple[int, int],
    target_pos: Tuple[int, int],
    env: ChakravyuhaEnvironment,
    occupied_positions: Set[Tuple[int, int]],
) -> Tuple[int, int]:
    """
    Greedy / local pathfinding step moving one cell closer to target_pos
    without stepping into walls or impassable positions.
    """
    cx, cy = current_pos
    tx, ty = target_pos
    
    if (cx, cy) == (tx, ty):
        return (cx, cy)
        
    candidates = []
    # 8-directional or 4-directional moves
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < env.grid_size and 0 <= ny < env.grid_size:
            if not env.is_wall((nx, ny)):
                dist = (nx - tx) ** 2 + (ny - ty) ** 2
                # Slightly penalize moving into occupied ally cells
                penalty = 5 if (nx, ny) in occupied_positions else 0
                candidates.append((dist + penalty, (nx, ny)))
                
    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]
        
    return current_pos


class BaseStrategy:
    """Base strategy defining lifecycle hooks for agent initialization, messaging, and action."""

    name: str = "base"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        """Spawns the attacker team at the outer approach zone."""
        raise NotImplementedError

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        """
        Executes perception, message exchange, and coordinated movement for this step.
        Returns total number of messages successfully delivered in this step.
        """
        raise NotImplementedError


class LoneEntryStrategy(BaseStrategy):
    """
    Strategy 1: Lone Entry (Abhimanyu enters the Chakravyuha alone).
    Followers do not enter. Abhimanyu advances rapidly towards the center
    using his complete knowledge of entry gates, but lacks exit knowledge.
    """

    name = "lone_entry"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        # Start just outside the outer ring near Gate 7
        g7 = env.entry_gates[7]
        start_pos = (min(config.grid_size - 1, g7[0] + 2), g7[1])
        
        abhimanyu = Attacker(
            agent_id="abhimanyu",
            role="infiltrator",
            pos=start_pos,
            health=config.abhimanyu_health,
            attack_power=config.abhimanyu_attack,
            vision_radius=config.vision_radius,
            comm_range=config.comm_range,
            known_entry_gates=env.entry_gates,  # Knows all entry gates IN
        )
        return [abhimanyu]

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        messages_sent = 0
        occupied: Set[Tuple[int, int]] = set()

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            a.scout_vision(env)
            target = self._decide_target(a, env)
            next_pos = get_next_step_towards(a.pos, target, env, occupied)
            a.pos = next_pos
            occupied.add(next_pos)

            # Check if breached into next ring
            current_ring = env.get_ring_of_point(a.pos)
            if current_ring <= config.num_rings:
                env.trigger_first_breach(a.pos)
                if current_ring < a.current_target_ring:
                    a.current_target_ring = current_ring
                    a.highest_ring_breached = max(a.highest_ring_breached, 8 - current_ring)

            if a.pos == env.center:
                a.has_reached_center = True

            # If reached center and made it outside
            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent

    def _decide_target(self, a: Attacker, env: ChakravyuhaEnvironment) -> Tuple[int, int]:
        if not a.has_reached_center:
            # Move sequentially through entry gates 7 -> 6 -> 5 -> ... -> 1 -> center
            for r in range(7, 0, -1):
                if env.get_ring_of_point(a.pos) > r:
                    return env.entry_gates[r]
            return env.center
        else:
            # Exiting phase: Abhimanyu has NO exit gate map!
            # If he has spotted any exit gate via vision, head for it; otherwise wander towards outside boundary
            current_ring = env.get_ring_of_point(a.pos)
            next_exit_ring = max(1, current_ring)
            if next_exit_ring in a.known_exit_gates:
                return a.known_exit_gates[next_exit_ring]
            # Wandering / guessing direction towards outer border
            return (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])


class BlindFollowStrategy(BaseStrategy):
    """
    Strategy 2: Blind Follow (Followers trail Abhimanyu with no communication).
    Followers do not know gate coordinates and attempt to trail Abhimanyu visually.
    Once Abhimanyu enters, Jayadratha locks the gate, stranding followers outside.
    """

    name = "blind_follow"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        g7 = env.entry_gates[7]
        start_pos = (min(config.grid_size - 1, g7[0] + 2), g7[1])
        
        abhimanyu = Attacker(
            agent_id="abhimanyu",
            role="infiltrator",
            pos=start_pos,
            health=config.abhimanyu_health,
            attack_power=config.abhimanyu_attack,
            vision_radius=config.vision_radius,
            comm_range=config.comm_range,
            known_entry_gates=env.entry_gates,
        )
        
        followers = []
        for i in range(1, config.num_followers + 1):
            f_pos = (min(config.grid_size - 1, start_pos[0] + 1), (start_pos[1] + i - 2) % config.grid_size)
            followers.append(
                Attacker(
                    agent_id=f"follower_{i}",
                    role="follower",
                    pos=f_pos,
                    health=config.follower_health,
                    attack_power=config.follower_attack,
                    vision_radius=config.vision_radius,
                    comm_range=0.0,  # No communication allowed
                    known_entry_gates={},  # Blank map
                )
            )
        return [abhimanyu] + followers

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        messages_sent = 0
        occupied: Set[Tuple[int, int]] = set()
        abhimanyu = attackers[0]

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            a.scout_vision(env)

            if a.role == "infiltrator":
                target = self._decide_abhimanyu_target(a, env)
            else:
                # Followers trail Abhimanyu if he's alive; otherwise move towards last known sight
                if abhimanyu.is_alive:
                    target = abhimanyu.pos
                else:
                    target = env.center

            next_pos = get_next_step_towards(a.pos, target, env, occupied)
            a.pos = next_pos
            occupied.add(next_pos)

            current_ring = env.get_ring_of_point(a.pos)
            if current_ring <= config.num_rings:
                env.trigger_first_breach(a.pos)
                if current_ring < a.current_target_ring:
                    a.current_target_ring = current_ring
                    a.highest_ring_breached = max(a.highest_ring_breached, 8 - current_ring)

            if a.pos == env.center:
                a.has_reached_center = True

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent

    def _decide_abhimanyu_target(self, a: Attacker, env: ChakravyuhaEnvironment) -> Tuple[int, int]:
        if not a.has_reached_center:
            for r in range(7, 0, -1):
                if env.get_ring_of_point(a.pos) > r:
                    return env.entry_gates[r]
            return env.center
        else:
            current_ring = env.get_ring_of_point(a.pos)
            next_exit_ring = max(1, current_ring)
            if next_exit_ring in a.known_exit_gates:
                return a.known_exit_gates[next_exit_ring]
            return (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])


class SharedMapStrategy(BaseStrategy):
    """
    Strategy 3: Shared Map (Agents broadcast discovered gates over message channel).
    When Abhimanyu or scouts locate an entry/exit gate, they broadcast it.
    Followers receive this coordinate if within communication range and update their maps.
    """

    name = "shared_map"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        g7 = env.entry_gates[7]
        start_pos = (min(config.grid_size - 1, g7[0] + 2), g7[1])
        
        abhimanyu = Attacker(
            agent_id="abhimanyu",
            role="infiltrator",
            pos=start_pos,
            health=config.abhimanyu_health,
            attack_power=config.abhimanyu_attack,
            vision_radius=config.vision_radius,
            comm_range=config.comm_range,
            known_entry_gates=env.entry_gates,
        )
        
        followers = []
        for i in range(1, config.num_followers + 1):
            f_pos = (min(config.grid_size - 1, start_pos[0] + 1), (start_pos[1] + i - 2) % config.grid_size)
            followers.append(
                Attacker(
                    agent_id=f"follower_{i}",
                    role="follower",
                    pos=f_pos,
                    health=config.follower_health,
                    attack_power=config.follower_attack,
                    vision_radius=config.vision_radius,
                    comm_range=config.comm_range,
                    known_entry_gates={},
                )
            )
        return [abhimanyu] + followers

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        messages_sent = 0
        occupied: Set[Tuple[int, int]] = set()

        # Step 1: Perceive & Scout
        for a in attackers:
            if a.is_alive:
                a.scout_vision(env)

        # Step 2: Broadcast maps
        for sender in attackers:
            if not sender.is_alive:
                continue
            # Package known gates
            msg = {
                "entry_gates": sender.known_entry_gates,
                "exit_gates": sender.known_exit_gates,
            }
            for receiver in attackers:
                if receiver != sender and receiver.is_alive:
                    if receiver.receive_message(msg, sender):
                        messages_sent += 1

        # Step 3: Process inboxes
        for a in attackers:
            if a.is_alive:
                a.process_inbox()

        # Step 4: Movement
        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            target = self._decide_target(a, env)
            next_pos = get_next_step_towards(a.pos, target, env, occupied)
            a.pos = next_pos
            occupied.add(next_pos)

            current_ring = env.get_ring_of_point(a.pos)
            if current_ring <= config.num_rings:
                env.trigger_first_breach(a.pos)
                if current_ring < a.current_target_ring:
                    a.current_target_ring = current_ring
                    a.highest_ring_breached = max(a.highest_ring_breached, 8 - current_ring)

            if a.pos == env.center:
                a.has_reached_center = True

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent

    def _decide_target(self, a: Attacker, env: ChakravyuhaEnvironment) -> Tuple[int, int]:
        if not a.has_reached_center:
            # Follow known entry gates
            current_ring = env.get_ring_of_point(a.pos)
            for r in range(min(7, current_ring), 0, -1):
                if r in a.known_entry_gates:
                    return a.known_entry_gates[r]
            return env.center
        else:
            current_ring = env.get_ring_of_point(a.pos)
            for r in range(max(1, current_ring), 8):
                if r in a.known_exit_gates:
                    return a.known_exit_gates[r]
            return (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])


class SplitExitStrategy(BaseStrategy):
    """
    Strategy 4: Split Exit (Dedicated scout subgroup searches for exit while strike force attacks).
    Abhimanyu and 1-2 strike warriors drive inward to breach the core.
    Scouts patrol intermediate rings to discover exit gates and broadcast them back to Abhimanyu.
    """

    name = "split_exit"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        g7 = env.entry_gates[7]
        start_pos = (min(config.grid_size - 1, g7[0] + 2), g7[1])
        
        abhimanyu = Attacker(
            agent_id="abhimanyu",
            role="infiltrator",
            pos=start_pos,
            health=config.abhimanyu_health,
            attack_power=config.abhimanyu_attack,
            vision_radius=config.vision_radius,
            comm_range=config.comm_range,
            known_entry_gates=env.entry_gates,
        )
        
        team = [abhimanyu]
        num_scouts = max(1, config.num_followers // 2)
        num_warriors = config.num_followers - num_scouts
        
        # Add strike warriors
        for i in range(1, num_warriors + 1):
            f_pos = (min(config.grid_size - 1, start_pos[0] + 1), (start_pos[1] + i) % config.grid_size)
            team.append(
                Attacker(
                    agent_id=f"warrior_{i}",
                    role="follower",
                    pos=f_pos,
                    health=config.follower_health,
                    attack_power=config.follower_attack,
                    vision_radius=config.vision_radius,
                    comm_range=config.comm_range,
                    known_entry_gates=dict(env.entry_gates),
                )
            )
            
        # Add scouts positioned along perimeter search trajectories
        for i in range(1, num_scouts + 1):
            s_pos = (max(0, start_pos[0] - 2), (start_pos[1] - i * 3) % config.grid_size)
            team.append(
                Attacker(
                    agent_id=f"scout_{i}",
                    role="scout",
                    pos=s_pos,
                    health=int(config.follower_health * 0.8),
                    attack_power=int(config.follower_attack * 0.8),
                    vision_radius=config.vision_radius * 1.5,  # Enhanced vision for scouts
                    comm_range=config.comm_range * 1.5,       # Stronger signaling horn
                    known_entry_gates=dict(env.entry_gates),
                )
            )
            
        return team

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        messages_sent = 0
        occupied: Set[Tuple[int, int]] = set()

        # Step 1: Perceive & Scout
        for a in attackers:
            if a.is_alive:
                a.scout_vision(env)

        # Step 2: Broadcast maps
        for sender in attackers:
            if not sender.is_alive:
                continue
            msg = {
                "entry_gates": sender.known_entry_gates,
                "exit_gates": sender.known_exit_gates,
            }
            for receiver in attackers:
                if receiver != sender and receiver.is_alive:
                    if receiver.receive_message(msg, sender):
                        messages_sent += 1

        # Step 3: Process inboxes
        for a in attackers:
            if a.is_alive:
                a.process_inbox()

        # Step 4: Movement
        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            target = self._decide_target(a, env)
            next_pos = get_next_step_towards(a.pos, target, env, occupied)
            a.pos = next_pos
            occupied.add(next_pos)

            current_ring = env.get_ring_of_point(a.pos)
            if current_ring <= config.num_rings:
                env.trigger_first_breach(a.pos)
                if current_ring < a.current_target_ring:
                    a.current_target_ring = current_ring
                    a.highest_ring_breached = max(a.highest_ring_breached, 8 - current_ring)

            if a.pos == env.center:
                a.has_reached_center = True

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent

    def _decide_target(self, a: Attacker, env: ChakravyuhaEnvironment) -> Tuple[int, int]:
        if a.role == "scout":
            # Scouts patrol around rings looking for exit gates
            for r in range(1, 8):
                if r not in a.known_exit_gates:
                    return env.exit_gates[r]
            return env.center
        else:
            if not a.has_reached_center:
                current_ring = env.get_ring_of_point(a.pos)
                for r in range(min(7, current_ring), 0, -1):
                    if r in a.known_entry_gates:
                        return a.known_entry_gates[r]
                return env.center
            else:
                current_ring = env.get_ring_of_point(a.pos)
                for r in range(max(1, current_ring), 8):
                    if r in a.known_exit_gates:
                        return a.known_exit_gates[r]
                return (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])


STRATEGY_REGISTRY = {
    "lone_entry": LoneEntryStrategy,
    "blind_follow": BlindFollowStrategy,
    "shared_map": SharedMapStrategy,
    "split_exit": SplitExitStrategy,
}


def get_strategy(strategy_name: str) -> BaseStrategy:
    """Factory function to retrieve strategy instance by name."""
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: '{strategy_name}'. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[strategy_name]()
