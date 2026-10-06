"""
Basic sanity tests for project modules.
"""

from sim.environment import ChakravyuhaEnvironment
from sim.agents import InfiltratorAgent, DefenderAgent
from sim.strategies import PenetrationStrategy, RingDefenseStrategy
from sim.engine import SimulationEngine


def test_environment_initialization():
    env = ChakravyuhaEnvironment(num_layers=7, grid_size=100)
    assert env.num_layers == 7
    assert env.grid_size == 100


def test_agent_creation():
    infiltrator = InfiltratorAgent(agent_id="abhimanyu")
    defender = DefenderAgent(agent_id="drona", layer=1)
    assert infiltrator.side == "pandava"
    assert defender.side == "kaurava"


def test_engine_initialization():
    engine = SimulationEngine()
    result = engine.run()
    assert result["status"] == "initialized"
