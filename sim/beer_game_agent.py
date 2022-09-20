from __future__ import annotations
from abc import abstractmethod
from statistics import mean

import numpy as np
from random import randint
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .beer_game import BeerGame

from .const import (
    AGENT_TYPE_BASESTOCK,
    AGENT_TYPE_BONSAI,
    AGENT_TYPE_MANUAL,
    AGENT_TYPE_RANDOM,
    AGENT_TYPE_STRM,
    DEMAND_DISTRIBUTION_NORMAL,
)

_LOGGER = logging.getLogger(__name__)


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

        self.current_costs = 0
        self.total_costs = 0

        self.inventory_level = self.sim.inventory_levels[self.agent_num]
        self.customer_orders_to_be_filled = 0  # to customer
        self.supplier_orders_to_be_delivered = 0  # to supplier
        self.arriving_shipments = {}  # from supplier
        self.arriving_orders = {}  # from customer
        self.previous_orders = {}

        if self.agent_num > 0:
            for i in range(self.sim.leadtime_orders_low[self.agent_num - 1]):
                if i > 0:
                    self.arriving_orders[i] = self.sim.arriving_orders[
                        self.agent_num - 1
                    ]
        for i in range(self.sim.leadtime_receiving_low[self.agent_num]):
            if i > 0:
                self.arriving_shipments[i] = self.sim.arriving_shipments[self.agent_num]
        self.c_h = self.sim.costs_holding[self.agent_num]
        self.c_p = self.sim.costs_shortage[self.agent_num]

        self.leadtime_orders = (
            self.sim.leadtime_orders_low[self.agent_num],
            self.sim.leadtime_orders_high[self.agent_num],
        )
        self.leadtime_receiving = (
            self.sim.leadtime_receiving_low[self.agent_num],
            self.sim.leadtime_receiving_high[self.agent_num],
        )

        self.a_b, self.b_b = self.set_a_b_values(
            float(np.mean((self.leadtime_receiving)) + np.mean((self.leadtime_orders)))
        )

    def place_order(self, time: int, action: int | None = None) -> None:
        """Handle the order of the agent"""
        order = min(self.get_order(time, action), self.sim.max_action)
        self.previous_orders[time] = order
        self.supplier_orders_to_be_delivered += order
        if self.supplier is not None:
            self.supplier.plan_order(time, order)
            return
        self.plan_shipment(time, order)

    def receive_items(self, time):
        """Updates the IL and customer_orders_to_be_filled at time t, after recieving "rec" number of items"""
        shipment = self.arriving_shipments.get(time, 0)
        self.inventory_level += shipment
        self.supplier_orders_to_be_delivered -= shipment

    def receive_order(self, time):
        """Updates the customer_orders_to_be_filled at time t, after recieving orders"""
        self.customer_orders_to_be_filled += self.arriving_orders.get(time, 0)

    def deliver_items(self, time):
        """Updates the backorder at time t, after delivering "del" number of items"""
        possible_shipment = min(self.inventory_level, self.customer_orders_to_be_filled)
        self.inventory_level -= possible_shipment
        self.customer_orders_to_be_filled -= possible_shipment
        if self.customer is not None:
            self.customer.plan_shipment(time, possible_shipment)
            return
        self.sim.total_delivered += possible_shipment
        self.sim.outstanding_demand -= possible_shipment

    def update_costs(self):
        """Update total_costs returns the total_costs at the current state"""
        # cost (holding + backorder) for one time unit
        self.current_costs = self.c_p * max(
            0, self.customer_orders_to_be_filled
        ) + self.c_h * max(0, self.inventory_level)
        self.total_costs += self.current_costs

    def plan_shipment(self, time: int, amount: int) -> None:
        """Add a shipment to arriving shipments."""
        if (
            shipment_time := time + randint(*self.leadtime_receiving) + 1
        ) in self.arriving_shipments:
            self.arriving_shipments[shipment_time] += amount
        else:
            self.arriving_shipments[shipment_time] = amount

    def plan_order(self, time: int, amount: int) -> None:
        """Add an order to arriving orders."""
        if (
            order_time := time + randint(*self.leadtime_orders) + 1
        ) in self.arriving_orders:
            self.arriving_orders[order_time] += amount
        else:
            self.arriving_orders[order_time] = amount

    @property
    def state(self):
        """This function returns a dict of the current state of the agent"""
        _LOGGER.debug("State for agent: %s", self.agent_num)
        _LOGGER.debug("   Inventory: %s", self.inventory_level)
        _LOGGER.debug(
            "   Customer orders to be filled: %s", self.customer_orders_to_be_filled
        )
        _LOGGER.debug(
            "   Supplier orders to be delivered: %s",
            self.supplier_orders_to_be_delivered,
        )
        _LOGGER.debug("    Arriving shipments: %s", self.arriving_shipments)
        _LOGGER.debug("    Arriving orders: %s", self.arriving_orders)
        _LOGGER.debug("    Current costs: %s", self.current_costs)
        _LOGGER.debug("    Total costs: %s", self.total_costs)
        return {
            "inventory_level": self.inventory_level,
            "customer_orders_to_be_filled": self.customer_orders_to_be_filled,
            "supplier_orders_to_be_delivered": self.supplier_orders_to_be_delivered,
            "arriving_shipments": self.next_arriving_shipments,
            "arriving_orders": self.next_arriving_orders,
            "current_costs": self.current_costs,
            "total_costs": self.total_costs,
        }

    @property
    def is_manufacturer(self) -> bool:
        """Returns True if the agent is a manufacturer"""
        return self.agent_num == len(self.sim.agents) - 1

    @property
    def is_retailer(self) -> bool:
        """Returns True if the agent is a retailer"""
        return self.agent_num == 0

    @property
    def supplier(self) -> BeerGameAgent | None:
        """Return the supplier of this agent."""
        assert self.sim.agents
        if self.is_manufacturer:
            return None
        return self.sim.agents[self.agent_num + 1]

    @property
    def customer(self) -> BeerGameAgent | None:
        """Return the supplier of this agent."""
        assert self.sim.agents
        if self.is_retailer:
            return None
        return self.sim.agents[self.agent_num - 1]

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
    def next_arriving_shipments(self) -> dict[int, int]:
        """Return the next arriving shipments"""
        return {
            (key - self.sim.time): val
            for key, val in self.arriving_shipments.items()
            if self.sim.time < key <= self.sim.time + 4
        }

    @property
    def next_arriving_orders(self) -> dict[int, int]:
        """Return the next arriving orders"""
        return {
            (key - self.sim.time): val
            for key, val in self.arriving_orders.items()
            if self.sim.time < key <= self.sim.time + 4
        }

    @property
    def previous_arrived_shipments(self) -> dict[int, int]:
        """Return the next arriving shipments"""
        return {
            (key - self.sim.time): val
            for key, val in self.arriving_shipments.items()
            if self.sim.time - 4 <= key <= self.sim.time
        }

    @property
    def previous_arrived_orders(self) -> dict[int, int]:
        """Return the next arriving orders"""
        return {
            (key - self.sim.time): val
            for key, val in self.arriving_orders.items()
            if self.sim.time - 4 <= key <= self.sim.time
        }

    @property
    def previous_orders_rel(self) -> dict[int, int]:
        """Return the next arriving orders"""
        return {
            (key - self.sim.time): val
            for key, val in self.previous_orders.items()
            if self.sim.time - 4 <= key <= self.sim.time
        }

    @abstractmethod
    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""


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

    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""
        if action is None:
            raise ValueError("Action cannot be None for a Bonsai agent.")
        return action


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

    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""
        return max(
            0,
            round(
                self.arriving_shipments.get(time, 0)
                + self.alpha_b * (self.inventory_level - self.a_b)
                + self.beta_b * (self.customer_orders_to_be_filled - self.b_b)
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
        self.basestock = 4

    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""
        prev_orders = self.previous_arrived_orders.values()
        if not prev_orders:
            prev_orders = [0]
        return max(
            0,
            round(
                self.basestock
                + 4 * mean(prev_orders)
                + self.customer_orders_to_be_filled
                - (self.supplier.customer_orders_to_be_filled if self.supplier else 0)
                - sum(self.previous_orders_rel.values()),
            ),
            0,
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

    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""
        return randint(0, 3)  # self.customer_orders_to_be_filled * 2)


class BeerGameAgentManual(BeerGameAgent):
    """Class for manual contributions."""

    def __init__(
        self,
        sim: "BeerGame",
        agent_num: int,
    ):
        """Initializes the manual agent class."""
        super().__init__(
            sim,
            agent_num,
            AGENT_TYPE_MANUAL,
        )

    def get_order(self, time: int, action: int | None = None) -> int:
        """Updates the action of the agent"""
        print("Agent State: ", self.state)
        new_order = int(input("Enter order (positive integers only): "))
        if new_order < 0:
            raise ValueError("Order cannot be negative.")
        return new_order
