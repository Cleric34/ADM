"""
tests/test_basic.py - Sanity and Module Integration Verification.
"""

from sim.environment import Config, ChakravyuhaEnvironment
from sim.agents import Attacker, Defender
from sim.strategies import LoneEntryStrategy, BlindFollowStrategy, SharedMapStrategy, SplitExitStrategy
from sim.engine import run_episode


def test_environment_initialization():
    config = Config(seed=42, num_rings=7, grid_size=31)
    env = ChakravyuhaEnvironment(config)
    assert env.config.num_rings == 7
    assert env.grid_size == 31
    assert len(env.entry_gates) == 7
    assert len(env.exit_gates) == 7


def test_agent_creation():
    infiltrator = Attacker(agent_id="abhimanyu", role="infiltrator", pos=(0, 0))
    defender = Defender(agent_id="drona", layer=1, pos=(15, 15))
    assert infiltrator.side == "pandava"
    assert defender.side == "kaurava"


def test_engine_initialization():
    config = Config(seed=42, max_steps=10)
    result = run_episode(config, "lone_entry")
    assert result["outcome"] in ["success", "wipeout", "timeout"]
