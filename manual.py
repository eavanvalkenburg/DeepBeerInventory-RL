#!/usr/bin/env python3
"""
MSFT Bonsai SDK3 Template for Simulator Integration using Python.

Copyright 2021 Microsoft

Usage:
  For registering simulator with the Bonsai service for training:
    python simulator_integration.py
    Then connect your registered simulator to a Brain via UI, or using the CLI: `bonsai simulator unmanaged connect -b <brain-name> -a <train-or-assess> -c BalancePole --simulator-name TrafficSchool
"""
from __future__ import annotations

import time
import logging

from sim.beer_game import BeerGame

_LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    _LOGGER.setLevel(logging.INFO)
    agent_types = ["manual", "basestock", "basestock", "basestock"]

    beergame = BeerGame()
    beergame.reset(agent_types=agent_types)

    try:
        while True:
            print("\nTime is now: ", beergame.time)
            beergame.step(0)
            time.sleep(0.1)
            print("\n")
            print("------------------")
            print(beergame.state)
    except KeyboardInterrupt:
        print("\n\n------------------")
        print("Total costs was {}".format(beergame.state["cumulative_costs"]))
        print("Total number of orders delivered: {}".format(beergame.total_delivered))
        print("Thank you for playing!")
