"""
tests/test_simulation.py - Comprehensive Unit and Integration Tests.

Validates:
1. Determinism and reproducibility with fixed random seed.
2. Jayadratha gate lockdown behavior following initial breach.
3. Limited vision radius boundaries.
4. Distance-bounded message delivery constraints.
5. Inward strength scaling for defenders.
6. Strategy instantiation and episode termination outcomes (including Oracle).
"""

import pytest
from sim.environment import Config, ChakravyuhaEnvironment
from sim.agents import Attacker, Defender
from sim.strategies import (
    OracleStrategy,
    LoneEntryStrategy,
    BlindFollowStrategy,
    SharedMapStrategy,
    SplitExitStrategy,
    get_strategy,
)
from sim.engine import run_episode, initialize_defenders


def test_fixed_seed_reproducibility():
    """Verify that identical seeds produce bit-exact simulation outcomes and telemetry."""
    config1 = Config(seed=123, difficulty="medium", comm_range=6.0, max_steps=50)
    config2 = Config(seed=123, difficulty="medium", comm_range=6.0, max_steps=50)
    
    res1 = run_episode(config1, "shared_map")
    res2 = run_episode(config2, "shared_map")
    
    assert res1["outcome"] == res2["outcome"], "Outcomes must match on identical seed"
    assert res1["steps"] == res2["steps"], "Step count must match on identical seed"
    assert res1["survivors"] == res2["survivors"], "Survivors must match on identical seed"
    assert res1["rings_breached"] == res2["rings_breached"], "Rings breached must match"
    assert res1["messages_sent"] == res2["messages_sent"], "Messages sent must match"


def test_jayadratha_blocks_followers_after_breach():
    """Verify that Jayadratha unit triggers and locks the outer gate after the first breach."""
    config = Config(seed=42)
    env = ChakravyuhaEnvironment(config)
    
    outer_gate = env.entry_gates[7]
    assert not env.jayadratha_active, "Jayadratha should be inactive before breach"
    assert not env.is_wall(outer_gate), "Outer gate must be open before breach"
    
    # Trigger first breach at outer gate
    env.trigger_first_breach(outer_gate)
    
    assert env.jayadratha_active, "Jayadratha must activate upon breach"
    assert env.is_wall(outer_gate), "Outer gate must become an impassable wall when Jayadratha is active"


def test_vision_radius_limits():
    """Verify that agents can only perceive entities and coordinates within their vision radius."""
    agent = Attacker(
        agent_id="test_scout",
        role="scout",
        pos=(15, 15),
        vision_radius=4.0,
    )
    
    # Within vision radius: distance = 3.0 <= 4.0
    assert agent.can_see((15, 18)) is True
    assert agent.can_see((15, 12)) is True
    
    # Outside vision radius: distance = 5.0 > 4.0
    assert agent.can_see((15, 20)) is False
    assert agent.can_see((10, 10)) is False


def test_messaging_respects_range():
    """Verify that messages are only received if sender is within receiver's communication range."""
    sender = Attacker(
        agent_id="sender",
        role="infiltrator",
        pos=(10, 10),
        comm_range=5.0,
    )
    
    near_receiver = Attacker(
        agent_id="near",
        role="follower",
        pos=(12, 12),
        comm_range=5.0,
    )
    
    far_receiver = Attacker(
        agent_id="far",
        role="follower",
        pos=(25, 25),
        comm_range=5.0,
    )
    
    msg = {"entry_gates": {7: (10, 10)}}
    
    delivered_near = near_receiver.receive_message(msg, sender)
    delivered_far = far_receiver.receive_message(msg, sender)
    
    assert delivered_near is True, "Nearby receiver should accept message"
    assert delivered_far is False, "Distant receiver must reject/drop message out of range"
    assert len(near_receiver.inbox) == 1
    assert len(far_receiver.inbox) == 0


def test_defender_power_scaling_by_ring():
    """Verify that inner ring defenders have strictly greater health and attack than outer ring defenders."""
    outer_def = Defender(agent_id="outer", layer=7, pos=(0, 0))
    middle_def = Defender(agent_id="mid", layer=4, pos=(0, 0))
    inner_def = Defender(agent_id="inner", layer=1, pos=(0, 0))
    
    assert outer_def.health < middle_def.health < inner_def.health
    assert outer_def.attack_power < middle_def.attack_power < inner_def.attack_power


def test_all_strategies_run():
    """Verify that all 5 strategies (including Oracle) execute successfully without exceptions."""
    strategies = ["oracle", "lone_entry", "blind_follow", "shared_map", "split_exit"]
    config = Config(seed=99, max_steps=20)
    
    for strat in strategies:
        res = run_episode(config, strat)
        assert res["outcome"] in ["success", "wipeout", "timeout"]
        assert 0 <= res["rings_breached"] <= 7
        assert res["steps"] > 0
        assert res["survivors"] >= 0
