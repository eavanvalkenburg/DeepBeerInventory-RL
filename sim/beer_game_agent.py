from abc import abstractmethod

import numpy as np
from random import randint

from .beer_game import BeerGame
from .const import (
    AGENT_TYPE_BASESTOCK,
    AGENT_TYPE_BONSAI,
    AGENT_TYPE_RANDOM,
    AGENT_TYPE_STRM,
    DEMAND_DISTRIBUTION_NORMAL,
)


class BeerGameAgent(object):
    """Here we want to define the agent class for the BeerGame"""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
        agent_type: str,
    ):
        """Initializes the agents with initial values for IL, OO and saves self.agentNum for recognizing the agents."""
        self.sim = sim
        self.agent_num = agent_num
        self.agent_type = agent_type

        self.cur_reward = 0
        self.action = 0

        self.inventory_level = self.sim.inventory_levels[self.agent_num]
        self.open_order = 0
        self.arriving_shipments = {0: 0}
        self.arriving_orders = {0: 0}

        if self.agent_num > 0:
            for i in range(self.sim.leadtime_orders_low[self.agent_num - 1]):
                self.arriving_orders[i] = self.sim.arriving_orders[self.agent_num - 1]
        for i in range(self.sim.leadtime_receiving_low[self.agent_num]):
            self.arriving_shipments[i] = self.sim.arriving_shipments[self.agent_num]
        self.c_h = self.sim.costs_holding[self.agent_num]
        self.c_p = self.sim.costs_shortage[self.agent_num]

        self.a_b, self.b_b = self.set_a_b_values(
            float(
                np.mean(
                    (
                        self.sim.leadtime_receiving_low[self.agent_num],
                        self.sim.leadtime_receiving_high[self.agent_num],
                    )
                )
                + np.mean(
                    (
                        self.sim.leadtime_orders_low[self.agent_num],
                        self.sim.leadtime_orders_high[self.agent_num],
                    )
                )
            )
        )

    def set_a_b_values(self, mean_leadtimes: float) -> tuple[float, float]:
        """Set the a_b and b_b values based on the demand distribution"""
        if self.sim.demand_distribution == DEMAND_DISTRIBUTION_NORMAL:
            return (self.sim.demand_mu, self.sim.demand_mu * mean_leadtimes)
        return (
            float(np.mean((self.sim.demand_low, self.sim.demand_high))),
            float(
                np.mean((self.sim.demand_high, self.sim.demand_low)) * mean_leadtimes
            ),
        )

    @property
    def sum_arriving_orders(self) -> int:
        """Sum all arriving orders"""
        return sum(self.arriving_orders.values())

    @property
    def sum_arriving_shipments(self) -> int:
        """Sum all arriving shipments"""
        return sum(self.arriving_shipments.values())

    @abstractmethod
    def update_action(self, time: int, action: int | None = None):
        """Updates the action of the agent"""

    def update_inventory(self, time):
        """Updates the IL and open_order at time t, after recieving "rec" number of items"""
        self.inventory_level = (
            self.inventory_level + self.arriving_shipments[time]
        )  # inverntory level update
        self.open_order = (
            self.open_order - self.arriving_shipments[time]
        )  # invertory in transient update

    def update_reward(self):
        """Update Reward returns the reward at the current state"""
        # cost (holding + backorder) for one time unit
        self.cur_reward = (
            -(
                self.c_p * max(0, -self.inventory_level)
                + self.c_h * max(0, self.inventory_level)
            )
            / 200.0
        )  # self.config.Ttest #

    @property
    def state(self):
        """This function returns a dict of the current state of the agent"""
        return {
            "inventory_level": self.inventory_level,
            "open_order": self.open_order,
            "arriving_shipments": self.arriving_shipments,
            "cur_reward": self.cur_reward,
            "action": self.action,
        }


class BeerGameAgentBonsai(BeerGameAgent):
    """Class for Bonsai Agent."""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
    ):
        """Initializes the bonsai agent class."""
        super().__init__(
            sim,
            agent_num,
            AGENT_TYPE_BONSAI,
        )

    def update_action(self, time: int, action: int | None = None):
        """Updates the action of the agent"""
        if action is None:
            raise ValueError("Action cannot be None for a Bonsai agent.")
        self.action = action


class BeerGameAgentSTRM(BeerGameAgent):
    """Class for STRM agent."""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
    ):
        """Initializes the STRM agent class."""
        super().__init__(
            sim,
            agent_num,
            AGENT_TYPE_STRM,
        )

        self.alpha_b = self.sim.strm_alpha[self.agent_num]
        self.beta_b = self.sim.strm_beta[self.agent_num]

    def update_action(self, time: int, action: int | None = None):
        """Updates the action of the agent"""
        self.action = max(
            0,
            round(
                self.arriving_shipments[time]
                + self.alpha_b * (self.inventory_level - self.a_b)
                + self.beta_b * (self.open_order - self.b_b)
            ),
        )


class BeerGameAgentBaseStock(BeerGameAgent):
    """Class for basestock agent."""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
    ):
        """Initializes the basestock agent class."""
        super().__init__(
            sim,
            agent_num,
            AGENT_TYPE_BASESTOCK,
        )
        self.basestock = 0

    def update_action(self, time: int, action: int | None = None):
        """Updates the action of the agent"""
        self.action = max(
            0,
            self.basestock
            - (self.inventory_level + self.open_order - self.arriving_orders[time]),
        )


class BeerGameAgentRandom(BeerGameAgent):
    """Class for random agent."""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
    ):
        """Initializes the random agent class."""
        super().__init__(
            sim,
            agent_num,
            AGENT_TYPE_RANDOM,
        )

    def update_action(self, time: int, action: int | None = None):
        """Updates the action of the agent"""
        self.action = randint(0, self.sim.max_action)
