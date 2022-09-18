from random import randint
from time import gmtime, strftime
from typing import Any

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


class BeerGame(object):
    """Main class for the simulation"""

    def __init__(self):
        """Initialize the game."""
        self.time = 0
        self.inventory_levels = [0, 0, 0, 0]
        self.arriving_orders = [0, 0, 0, 0]
        self.arriving_shipments = [0, 0, 0, 0]
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
            AGENT_TYPE_STRM,
            AGENT_TYPE_STRM,
            AGENT_TYPE_STRM,
        ],
        costs_shortage: list[float] = [2, 1, 0, 0],
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
        # self.update_open_orders()

    @property
    def num_agents(self) -> int:
        """Return the number of agents."""
        return len(self.agent_types)

    def update_open_orders(self):
        """Update the open orders of all agents."""
        for k in range(0, self.num_agents):
            if k < self.num_agents - 1:
                self.agents[k].open_order = (
                    self.agents[k + 1].sum_arriving_orders
                    + self.agents[k].sum_arriving_shipments
                )
            else:
                self.agents[k].open_order = self.agents[k].sum_arriving_shipments

    def step(self, action: int) -> None:
        """
        Move the state of the simulation forward one time unit.
        The action is placed first because of the demands for Bonsai. Otherwise it would be the last step, this is why the time is increased second.

        Args:
            action: a dict with a key 'command'.
        """
        self.place_orders(action)
        self.time += 1
        self.receive_incoming_shipments()
        self.receive_incoming_orders()
        self.deliver_shipments()

        # self.handle_action(action)
        # self.next()

    def place_orders(self, action: int | None) -> None:
        """Place the new orders."""
        for agent in self.agents:
            # determine new order
            agent.update_orders(self.time, action)
            # add new order to arriving orders or supplier with delay (leadtime)
            if agent.agent_num != 4:
                self.agents[agent.agent_num + 1].arriving_orders[
                    self.time + randint(*agent.leadtime_orders)
                ] += agent.order
            else:
                agent.arriving_shipments[
                    self.time + randint(*agent.leadtime_receiving) + 1
                ] += agent.order

    def receive_incoming_shipments(self) -> None:
        """Receive the incoming shipments for the current time step."""
        for agent in self.agents:
            agent.inventory_level += agent.arriving_shipments[self.time]

    def receive_incoming_orders(self) -> None:
        """Receive the incoming orders for the current time step."""
        for agent in self.agents:
            agent.open_order += agent.arriving_orders[self.time]

    def deliver_shipments(self) -> None:
        """Deliver the shipments for the current time step."""
        for agent in self.agents:
            lead_time_rec = randint(*agent.leadtime_receiving)
            if agent.agent_num != 4:
                possible_shipment = min(
                    self.agents[agent.agent_num + 1].open_order,
                    self.agents[agent.agent_num + 1].inventory_level,
                )
                agent.arriving_shipments[self.time + lead_time_rec] += possible_shipment
                self.agents[agent.agent_num + 1].open_order -= possible_shipment

    # def handle_action(self, action):
    #     """Handle the action."""
    #     assert self.agents
    #     lead_time = randint(
    #         self.leadtime_receiving_low[0],
    #         self.leadtime_receiving_high[0],
    #     )
    #     self.agents[0].arriving_orders[self.time] += self.new_demand

    # def next(self):
    #     """Move the simulation forward."""
    #     assert self.agents
    #     lead_time_in = randint(
    #         self.leadtime_receiving_low[-1], self.leadtime_receiving_high[-1]
    #     )
    #     self.agents[-1].arriving_shipments[self.time + lead_time_in] += self.agents[
    #         -1
    #     ].action

    #     for k in range(len(self.agents) - 1, -1, -1):  # [3,2,1,0]
    #         self.agents[k].update_inventory(self.time)
    #         possible_shipment = min(
    #             self.agents[k].inventory_level
    #             + self.agents[k].arriving_shipments[self.time],
    #             -self.agents[k].inventory_level
    #             + self.agents[k].arriving_orders[self.time],
    #         )
    #         if self.agents[k].agent_num > 0:
    #             lead_time_in = randint(
    #                 self.leadtime_receiving_low[k], self.leadtime_receiving_high[k]
    #             )
    #             self.agents[k - 1].arriving_shipments[
    #                 self.time + lead_time_in
    #             ] += possible_shipment
    #         # update IL
    #         self.agents[k].inventory_level -= self.agents[k].arriving_orders[self.time]
    #         self.agents[k].update_reward()

    @property
    def state(self) -> dict[str, Any]:
        """Return the state of the sim."""
        assert self.agents
        states = [agent.state for agent in self.agents]
        return {
            "inventory_levels": [a["inventory_level"] for a in states],
            "open_orders": [a["open_order"] for a in states],
            "arriving_shipments": [a["arriving_shipments"] for a in states],
            "cur_rewards": [a["cur_rewards"] for a in states],
            "actions": [a["action"] for a in states],
        }

    @property
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
