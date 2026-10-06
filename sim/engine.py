"""
sim/engine.py - Simulation Execution Engine for Chakravyuha.

Orchestrates episode runs, defender initialization, patrol/combat mechanics,
and telemetry collection for single and batch experiments.
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from sim.environment import Config, ChakravyuhaEnvironment
from sim.agents import Attacker, Defender
from sim.strategies import BaseStrategy, get_strategy


def initialize_defenders(env: ChakravyuhaEnvironment, config: Config) -> List[Defender]:
    """
    Instantiates defenders along each of the 7 concentric rings based on difficulty.
    Defenders are distributed evenly across the ring perimeter, avoiding exact entry/exit gates.
    """
    defenders: List[Defender] = []
    def_counts = config.defenders_per_ring.get(config.difficulty, config.defenders_per_ring["medium"])
    
    for r in range(1, config.num_rings + 1):
        count = def_counts.get(r, 4)
        ring_cells = sorted(list(env.ring_cells[r]))
        # Filter out entry and exit gates so the passageways aren't permanently obstructed at t=0
        available_cells = [c for c in ring_cells if c != env.entry_gates[r] and c != env.exit_gates[r]]
        
        if not available_cells:
            available_cells = ring_cells
            
        step_stride = max(1, len(available_cells) // count)
        for i in range(count):
            idx = (i * step_stride) % len(available_cells)
            pos = available_cells[idx]
            defender_id = f"def_r{r}_{i+1}"
            defenders.append(
                Defender(
                    agent_id=defender_id,
                    layer=r,
                    pos=pos,
                    vision_radius=config.vision_radius,
                    comm_range=config.comm_range,
                )
            )
            
    return defenders


def step_defenders(defenders: List[Defender], attackers: List[Attacker], env: ChakravyuhaEnvironment) -> None:
    """
    Updates defender positions: defenders patrol within their ring layer and
    step towards any visible alive attackers within their perception radius.
    """
    alive_attackers = [a for a in attackers if a.is_alive and not a.has_exited]
    
    for d in defenders:
        if not d.is_alive:
            continue
            
        # Check for visible attackers
        spotted_attacker = None
        min_dist = float("inf")
        for a in alive_attackers:
            dist = d.distance_to(a.pos)
            if dist <= d.vision_radius and dist < min_dist:
                min_dist = dist
                spotted_attacker = a
                
        if spotted_attacker is not None:
            # Step towards attacker while staying within or near their ring
            cx, cy = d.pos
            tx, ty = spotted_attacker.pos
            candidates = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < env.grid_size and 0 <= ny < env.grid_size:
                    ring = env.get_ring_of_point((nx, ny))
                    # Defenders patrol around their designated layer (+/- 1 ring tolerance)
                    if abs(ring - d.layer) <= 1:
                        dist = (nx - tx) ** 2 + (ny - ty) ** 2
                        candidates.append((dist, (nx, ny)))
                        
            if candidates:
                candidates.sort(key=lambda x: x[0])
                d.pos = candidates[0][1]


def resolve_combat(attackers: List[Attacker], defenders: List[Defender]) -> None:
    """
    Resolves simultaneous combat between attackers and defenders in contact / melee range (<= 1.5 units).
    """
    alive_attackers = [a for a in attackers if a.is_alive and not a.has_exited]
    alive_defenders = [d for d in defenders if d.is_alive]
    
    for a in alive_attackers:
        for d in alive_defenders:
            if not d.is_alive or not a.is_alive:
                continue
            if a.distance_to(d.pos) <= 1.5:
                # Mutual combat exchange
                d.take_damage(a.attack_power)
                a.take_damage(d.attack_power)


def run_episode(
    config: Config,
    strategy: Union[str, BaseStrategy],
    record_history: bool = False,
) -> Dict[str, Any]:
    """
    Executes a single complete simulation episode.

    Args:
        config: Simulation configuration parameters.
        strategy: Strategy name or instance ('lone_entry', 'blind_follow', 'shared_map', 'split_exit').
        record_history: If True, snapshots environment and agent states at each step.

    Returns:
        Dict containing:
            - outcome: 'success', 'wipeout', or 'timeout'
            - steps: Total elapsed steps
            - survivors: Number of alive attackers at end
            - rings_breached: Maximum number of rings breached (0..7)
            - messages_sent: Total number of communication messages delivered
            - history (optional): List of step snapshots if record_history=True
    """
    if isinstance(strategy, str):
        strat_obj = get_strategy(strategy)
    else:
        strat_obj = strategy

    env = ChakravyuhaEnvironment(config)
    attackers = strat_obj.setup_attackers(env, config)
    defenders = initialize_defenders(env, config)

    total_messages = 0
    max_rings_breached = 0
    history: List[Dict[str, Any]] = []

    step = 0
    outcome = "timeout"

    while step < config.max_steps:
        step += 1

        if record_history:
            history.append({
                "step": step,
                "env": env,
                "attackers": [
                    {
                        "id": a.agent_id,
                        "role": a.role,
                        "pos": a.pos,
                        "health": a.health,
                        "alive": a.is_alive,
                        "reached_center": a.has_reached_center,
                        "exited": a.has_exited,
                    }
                    for a in attackers
                ],
                "defenders": [
                    {
                        "id": d.agent_id,
                        "layer": d.layer,
                        "pos": d.pos,
                        "health": d.health,
                        "alive": d.is_alive,
                        "color": d.strength_color,
                    }
                    for d in defenders
                ],
                "jayadratha_active": env.jayadratha_active,
            })

        # 1. Attacker perception, communication, and movement
        step_msgs = strat_obj.coordinate_and_step(attackers, defenders, env, config)
        total_messages += step_msgs

        # 2. Defender patrol & intercept
        step_defenders(defenders, attackers, env)

        # 3. Combat resolution
        resolve_combat(attackers, defenders)

        # 4. Update metrics
        for a in attackers:
            if a.highest_ring_breached > max_rings_breached:
                max_rings_breached = a.highest_ring_breached
            if a.has_reached_center and max_rings_breached < 7:
                max_rings_breached = 7

        # 5. Check terminal conditions
        # Success: at least one attacker has reached center and made it outside
        if any(a.has_exited for a in attackers):
            outcome = "success"
            break

        # Wipeout: all attackers eliminated
        if not any(a.is_alive for a in attackers):
            outcome = "wipeout"
            break

    survivors = sum(1 for a in attackers if a.is_alive)

    result = {
        "outcome": outcome,
        "steps": step,
        "survivors": survivors,
        "rings_breached": max_rings_breached,
        "messages_sent": total_messages,
    }

    if record_history:
        result["history"] = history

    return result
