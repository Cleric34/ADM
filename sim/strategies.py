"""
sim/strategies.py - Attacker Multi-Agent Coordination Strategies.

Implements tactical strategies under incomplete information:
1. `oracle`: Idealized baseline where every attacker knows all entry and exit gates.
2. `lone_entry`: Abhimanyu enters the formation completely alone.
3. `blind_follow`: Followers trail Abhimanyu's position with zero communication.
4. `shared_map`: Agents continuously broadcast discovered entry and exit gates over the message channel.
5. `split_exit`: A designated scout subgroup explores outer rings to find exit routes while the strike force penetrates inwards.
"""

from collections import deque
from typing import List, Dict, Tuple, Optional, Any, Set
import numpy as np
from sim.agents import Attacker, Defender, Agent
from sim.environment import ChakravyuhaEnvironment, Config


def bfs_next_step(
    start: Tuple[int, int],
    target: Tuple[int, int],
    env: ChakravyuhaEnvironment,
    occupied: Optional[Set[Tuple[int, int]]] = None,
) -> Tuple[int, int]:
    """
    Breadth-First Search pathfinding navigating around concentric formation walls
    to determine the optimal next grid step towards the target waypoint.
    """
    if start == target:
        return start
    if occupied is None:
        occupied = set()

    queue = deque([start])
    visited = {start: None}

    while queue:
        curr = queue.popleft()
        if curr == target:
            break
        cx, cy = curr
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < env.grid_size and 0 <= ny < env.grid_size:
                if (nx, ny) not in visited:
                    if not env.is_wall((nx, ny)) or (nx, ny) == target:
                        visited[(nx, ny)] = curr
                        queue.append((nx, ny))

    if target not in visited:
        candidates = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = start[0] + dx, start[1] + dy
            if 0 <= nx < env.grid_size and 0 <= ny < env.grid_size:
                if not env.is_wall((nx, ny)):
                    dist = (nx - target[0]) ** 2 + (ny - target[1]) ** 2
                    candidates.append((dist, (nx, ny)))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return start

    curr = target
    path = []
    while curr is not None:
        path.append(curr)
        curr = visited[curr]
    path.reverse()
    return path[1] if len(path) > 1 else start


def get_next_step_towards(
    current_pos: Tuple[int, int],
    target_pos: Tuple[int, int],
    env: ChakravyuhaEnvironment,
    occupied_positions: Set[Tuple[int, int]],
) -> Tuple[int, int]:
    """Compatibility alias wrapping BFS next step."""
    return bfs_next_step(current_pos, target_pos, env, occupied_positions)


class BaseStrategy:
    """Base strategy defining lifecycle hooks for agent initialization, messaging, and action."""

    name: str = "base"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        raise NotImplementedError

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        raise NotImplementedError


class OracleStrategy(BaseStrategy):
    """
    Strategy 0: Oracle Baseline.
    All attacker agents possess complete a priori knowledge of ALL entry gates ($G_7 \to G_1$)
    and ALL exit gates ($E_1 \to E_7$). Serves as theoretical upper-bound benchmark.
    """

    name = "oracle"

    def setup_attackers(self, env: ChakravyuhaEnvironment, config: Config) -> List[Attacker]:
        g7 = env.entry_gates[7]
        start_pos = (min(config.grid_size - 1, g7[0] + 2), g7[1])

        team = []
        abhimanyu = Attacker(
            agent_id="oracle_abhimanyu",
            role="infiltrator",
            pos=start_pos,
            health=config.abhimanyu_health,
            attack_power=config.abhimanyu_attack,
            vision_radius=config.vision_radius,
            comm_range=config.comm_range,
            known_entry_gates=dict(env.entry_gates),
        )
        abhimanyu.known_exit_gates = dict(env.exit_gates)
        abhimanyu.target_entry_ring = 7
        abhimanyu.target_exit_ring = 1
        team.append(abhimanyu)
        return team

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        occupied: Set[Tuple[int, int]] = set()

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            if not hasattr(a, "target_entry_ring"):
                a.target_entry_ring = 7
                a.target_exit_ring = 1

            if not a.has_reached_center:
                if a.target_entry_ring > 0:
                    target = env.entry_gates[a.target_entry_ring]
                    if a.pos == target:
                        a.target_entry_ring -= 1
                        target = env.entry_gates[a.target_entry_ring] if a.target_entry_ring > 0 else env.center
                else:
                    target = env.center
            else:
                if a.target_exit_ring <= 7:
                    target = env.exit_gates[a.target_exit_ring]
                    if a.pos == target:
                        a.target_exit_ring += 1
                        target = env.exit_gates[a.target_exit_ring] if a.target_exit_ring <= 7 else (0, a.pos[1])
                else:
                    target = (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])

            next_pos = bfs_next_step(a.pos, target, env, occupied)
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
                a.highest_ring_breached = 7

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return 0


class LoneEntryStrategy(BaseStrategy):
    """
    Strategy 1: Lone Entry (Abhimanyu enters the Chakravyuha alone).
    Followers do not enter. Abhimanyu advances rapidly towards the center
    using his knowledge of entry gates, but has no prior exit map.
    """

    name = "lone_entry"

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
            known_entry_gates=dict(env.entry_gates),
        )
        abhimanyu.target_entry_ring = 7
        abhimanyu.target_exit_ring = 1
        return [abhimanyu]

    def coordinate_and_step(
        self,
        attackers: List[Attacker],
        defenders: List[Defender],
        env: ChakravyuhaEnvironment,
        config: Config,
    ) -> int:
        occupied: Set[Tuple[int, int]] = set()

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            a.scout_vision(env)
            if not hasattr(a, "target_entry_ring"):
                a.target_entry_ring = 7
                a.target_exit_ring = 1

            if not a.has_reached_center:
                if a.target_entry_ring > 0:
                    target = env.entry_gates[a.target_entry_ring]
                    if a.pos == target:
                        a.target_entry_ring -= 1
                        target = env.entry_gates[a.target_entry_ring] if a.target_entry_ring > 0 else env.center
                else:
                    target = env.center
            else:
                # Exiting phase: use scouted exit gates if known; otherwise head towards border
                current_ring = env.get_ring_of_point(a.pos)
                if current_ring in a.known_exit_gates:
                    target = a.known_exit_gates[current_ring]
                else:
                    target = (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])

            next_pos = bfs_next_step(a.pos, target, env, occupied)
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
                a.highest_ring_breached = 7

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return 0


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
            known_entry_gates=dict(env.entry_gates),
        )
        abhimanyu.target_entry_ring = 7
        abhimanyu.target_exit_ring = 1

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
                    comm_range=0.0,
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
        occupied: Set[Tuple[int, int]] = set()
        abhimanyu = attackers[0]

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            a.scout_vision(env)
            if not hasattr(a, "target_entry_ring"):
                a.target_entry_ring = 7
                a.target_exit_ring = 1

            if a.role == "infiltrator":
                if not a.has_reached_center:
                    if a.target_entry_ring > 0:
                        target = env.entry_gates[a.target_entry_ring]
                        if a.pos == target:
                            a.target_entry_ring -= 1
                            target = env.entry_gates[a.target_entry_ring] if a.target_entry_ring > 0 else env.center
                    else:
                        target = env.center
                else:
                    current_ring = env.get_ring_of_point(a.pos)
                    if current_ring in a.known_exit_gates:
                        target = a.known_exit_gates[current_ring]
                    else:
                        target = (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])
            else:
                target = abhimanyu.pos if abhimanyu.is_alive else env.center

            next_pos = bfs_next_step(a.pos, target, env, occupied)
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
                a.highest_ring_breached = 7

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return 0


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
            known_entry_gates=dict(env.entry_gates),
        )
        abhimanyu.target_entry_ring = 7
        abhimanyu.target_exit_ring = 1

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

        for a in attackers:
            if a.is_alive:
                a.scout_vision(env)

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

        for a in attackers:
            if a.is_alive:
                a.process_inbox()

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            if not hasattr(a, "target_entry_ring"):
                a.target_entry_ring = 7
                a.target_exit_ring = 1

            if not a.has_reached_center:
                if a.target_entry_ring in a.known_entry_gates:
                    target = a.known_entry_gates[a.target_entry_ring]
                    if a.pos == target:
                        a.target_entry_ring -= 1
                        target = a.known_entry_gates.get(a.target_entry_ring, env.center)
                else:
                    target = env.center
            else:
                if a.target_exit_ring in a.known_exit_gates:
                    target = a.known_exit_gates[a.target_exit_ring]
                    if a.pos == target:
                        a.target_exit_ring += 1
                        target = a.known_exit_gates.get(a.target_exit_ring, (0, a.pos[1]))
                else:
                    target = (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])

            next_pos = bfs_next_step(a.pos, target, env, occupied)
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
                a.highest_ring_breached = 7

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent


class SplitExitStrategy(BaseStrategy):
    """
    Strategy 4: Split Exit (Dedicated scout subgroup searches for exit while strike force attacks).
    Abhimanyu and strike warriors drive inward to breach the core.
    Scouts patrol intermediate rings to discover exit gates and broadcast them back.
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
            known_entry_gates=dict(env.entry_gates),
        )
        abhimanyu.target_entry_ring = 7
        abhimanyu.target_exit_ring = 1

        team = [abhimanyu]
        num_scouts = max(1, config.num_followers // 2)
        num_warriors = config.num_followers - num_scouts

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

        for i in range(1, num_scouts + 1):
            s_pos = (max(0, start_pos[0] - 2), (start_pos[1] - i * 3) % config.grid_size)
            team.append(
                Attacker(
                    agent_id=f"scout_{i}",
                    role="scout",
                    pos=s_pos,
                    health=int(config.follower_health * 0.8),
                    attack_power=int(config.follower_attack * 0.8),
                    vision_radius=config.vision_radius * 1.5,
                    comm_range=config.comm_range * 1.5,
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

        for a in attackers:
            if a.is_alive:
                a.scout_vision(env)

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

        for a in attackers:
            if a.is_alive:
                a.process_inbox()

        for a in attackers:
            if not a.is_alive or a.has_exited:
                continue

            if not hasattr(a, "target_entry_ring"):
                a.target_entry_ring = 7
                a.target_exit_ring = 1

            if a.role == "scout":
                target = env.center
                for r in range(1, 8):
                    if r not in a.known_exit_gates:
                        target = env.exit_gates[r]
                        break
            else:
                if not a.has_reached_center:
                    if a.target_entry_ring in a.known_entry_gates:
                        target = a.known_entry_gates[a.target_entry_ring]
                        if a.pos == target:
                            a.target_entry_ring -= 1
                            target = a.known_entry_gates.get(a.target_entry_ring, env.center)
                    else:
                        target = env.center
                else:
                    if a.target_exit_ring in a.known_exit_gates:
                        target = a.known_exit_gates[a.target_exit_ring]
                        if a.pos == target:
                            a.target_exit_ring += 1
                            target = a.known_exit_gates.get(a.target_exit_ring, (0, a.pos[1]))
                    else:
                        target = (0, a.pos[1]) if a.pos[0] < env.center[0] else (env.grid_size - 1, a.pos[1])

            next_pos = bfs_next_step(a.pos, target, env, occupied)
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
                a.highest_ring_breached = 7

            if a.has_reached_center and current_ring > config.num_rings:
                a.has_exited = True

        return messages_sent


STRATEGY_REGISTRY = {
    "oracle": OracleStrategy,
    "lone_entry": LoneEntryStrategy,
    "blind_follow": BlindFollowStrategy,
    "shared_map": SharedMapStrategy,
    "split_exit": SplitExitStrategy,
}


def get_strategy(strategy_name: str) -> BaseStrategy:
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: '{strategy_name}'. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[strategy_name]()
