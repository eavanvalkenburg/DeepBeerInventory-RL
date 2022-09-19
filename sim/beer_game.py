from random import randint
from time import gmtime, strftime
from typing import Any
import logging
import numpy as np

from .beer_game_agent import (
    BeerGameAgent,
    BeerGameAgentBaseStock,
    BeerGameAgentBonsai,
    BeerGameAgentRandom,
    BeerGameAgentSTRM,
)
from .const import (
    AGENT_TYPE_BASESTOCK,
    AGENT_TYPE_BONSAI,
    AGENT_TYPE_RANDOM,
    AGENT_TYPE_STRM,
    DEMAND_DISTRIBUTION_NORMAL,
    DEMAND_DISTRIBUTION_UNIFORM,
)

_LOGGER = logging.getLogger(__name__)


class BeerGame(object):
    """Main class for the simulation"""

    def __init__(self):
        """Initialize the game."""
        self.time = 0
        self.inventory_levels = [0, 0, 0, 0]
        self.arriving_orders = [0, 0, 0, 0]
        self.arriving_shipments = [0, 0, 0, 0]
        self.total_delivered: int = 0
        self.agents: list[BeerGameAgent] = []
        self.max_action: int = 61

        self.demand_distribution: str = DEMAND_DISTRIBUTION_UNIFORM  # "normal"
        self.demand_low: int = 0
        self.demand_high: int = 3
        self.demand_mu: float = 10
        self.demand_sigma: float = 2

        self.agent_types: list[str] = [
            AGENT_TYPE_BONSAI,
            AGENT_TYPE_STRM,
            AGENT_TYPE_STRM,
            AGENT_TYPE_STRM,
        ]
        self.costs_shortage: list[float] = [2, 1, 0, 0]
        self.costs_holding: list[float] = [2, 2, 2, 2]
        self.strm_alpha: list[float] = [-0.5, -0.5, -0.5, -0.5]
        self.strm_beta: list[float] = [-0.2, -0.2, -0.2, -0.2]
        self.leadtime_receiving_low: list[int] = [2, 2, 2, 4]
        self.leadtime_receiving_high: list[int] = [2, 2, 2, 4]
        self.leadtime_orders_low: list[int] = [2, 2, 2, 0]
        self.leadtime_orders_high: list[int] = [2, 2, 2, 0]

        self.reset()

    def reset(
        self,
        demand_distribution: str = DEMAND_DISTRIBUTION_UNIFORM,  # "normal"
        demand_low: int = 0,  # for uniform
        demand_high: int = 3,  # for uniform
        demand_mu: float = 10,  # for normal
        demand_sigma: float = 2,  # for normal
        action_high: int = 2,
        agent_types: list[str] = [
            AGENT_TYPE_BONSAI,
            AGENT_TYPE_RANDOM,
            AGENT_TYPE_RANDOM,
            AGENT_TYPE_RANDOM,
        ],
        costs_shortage: list[float] = [2, 0, 0, 0],
        costs_holding: list[float] = [2, 2, 2, 2],
        strm_alpha: list[float] = [-0.5, -0.5, -0.5, -0.5],
        strm_beta: list[float] = [-0.2, -0.2, -0.2, -0.2],
        leadtime_receiving_low: list[int] = [2, 2, 2, 4],
        leadtime_receiving_high: list[int] = [2, 2, 2, 4],
        leadtime_orders_low: list[int] = [2, 2, 2, 0],
        leadtime_orders_high: list[int] = [2, 2, 2, 0],
        inventory_initial: list[int] = [0, 0, 0, 0],
        arriving_orders_initial: list[int] = [0, 0, 0, 0],
        arriving_shipments_initial: list[int] = [0, 0, 0, 0],
    ) -> None:
        """Reset the sim."""
        self.time = 0
        self.inventory_levels = inventory_initial
        self.arriving_orders = arriving_orders_initial
        self.arriving_shipments = arriving_shipments_initial
        self.total_delivered = 0
        self.outstanding_demand = 0

        self.demand_distribution = demand_distribution
        self.demand_low = demand_low
        self.demand_high = demand_high
        self.demand_mu = demand_mu
        self.demand_sigma = demand_sigma

        self.agent_types = agent_types
        self.costs_shortage = costs_shortage
        self.costs_holding = costs_holding
        self.strm_alpha = strm_alpha
        self.strm_beta = strm_beta
        self.leadtime_receiving_low = leadtime_receiving_low
        self.leadtime_receiving_high = leadtime_receiving_high
        self.leadtime_orders_low = leadtime_orders_low
        self.leadtime_orders_high = leadtime_orders_high

        self.max_action = int(
            max(
                action_high * 30 + 1,
                48 if self.demand_distribution == DEMAND_DISTRIBUTION_UNIFORM else 112,
            )
        )

        self.create_agents()

    @property
    def manufacturing_agent_num(self) -> int:
        """Return the manufacturing agent number."""
        return self.agents[-1].agent_num

    @property
    def num_agents(self) -> int:
        """Return the number of agents."""
        return len(self.agent_types)

    def step(self, action: int) -> None:
        """
        Move the state of the simulation forward one time unit.
        The action is placed first because of the demands for Bonsai. Otherwise it would be the last step, this is why the time is increased second.

        Args:
            action: a dict with a key 'command'.
        """
        assert self.agents
        _LOGGER.debug("Updating orders")
        new = self.new_demand()
        self.agents[0].plan_order(self.time, new)
        self.outstanding_demand += new

        for agent in self.agents:
            agent.place_order(self.time, action)
        _LOGGER.debug("Increasing time")
        self.time += 1
        _LOGGER.debug("Time is now: %s", self.time)
        _LOGGER.debug("Receiving Incoming Shipments")
        for agent in self.agents:
            agent.receive_items(self.time)
        _LOGGER.debug("Receiving Incoming Orders")
        for agent in self.agents:
            agent.receive_order(self.time)
        _LOGGER.debug("Delivering shipments")
        for agent in self.agents:
            agent.deliver_items(self.time)
        _LOGGER.debug("Updating costs")
        for agent in self.agents:
            agent.update_costs()

    @property
    def state(self) -> dict[str, Any]:
        """Return the state of the sim."""
        assert self.agents
        states = [agent.state for agent in self.agents]
        return {
            "inventory_levels": [a["inventory_level"] for a in states],
            "customer_orders_to_be_filled": [
                a["customer_orders_to_be_filled"] for a in states
            ],
            "supplier_orders_to_be_delivered": [
                a["supplier_orders_to_be_delivered"] for a in states
            ],
            "arriving_shipments": [a["arriving_shipments"] for a in states],
            "arriving_orders": [a["arriving_orders"] for a in states],
            "current_costs": [a["current_costs"] for a in states],
            "total_costs": [a["total_costs"] for a in states],
            "cumulative_costs": sum([a["total_costs"] for a in states]),
            "total_delivered": self.total_delivered,
            "outstanding_demand": self.outstanding_demand,
            "time": self.time,
        }

    def new_demand(self) -> int:
        """Get a new demand."""
        if self.demand_distribution == DEMAND_DISTRIBUTION_NORMAL:
            return int(np.random.normal(self.demand_mu, self.demand_sigma))
        return randint(self.demand_low, self.demand_high)

    def create_agents(self) -> None:
        """Create the agents."""
        self.agents = []
        for i in range(self.num_agents):
            if self.agent_types[i] == AGENT_TYPE_BONSAI:
                self.agents.append(BeerGameAgentBonsai(self, i))
                continue
            if self.agent_types[i] == AGENT_TYPE_RANDOM:
                self.agents.append(BeerGameAgentRandom(self, i))
                continue
            if self.agent_types[i] == AGENT_TYPE_BASESTOCK:
                self.agents.append(BeerGameAgentBaseStock(self, i))
                continue
            if self.agent_types[i] == AGENT_TYPE_STRM:
                self.agents.append(BeerGameAgentSTRM(self, i))
                continue
