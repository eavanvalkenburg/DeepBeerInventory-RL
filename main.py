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

import aiohttp
import argparse
import asyncio
import logging
from functools import partial

from helpers import set_env
from simulator_session import (
    SimulatorSession,
)

_LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bonsai and Simulator Integration...")
    parser.add_argument(
        "--log-level",
        type=str,
        help="Log level used by the logging package, defaults to info.",
        default="INFO",
    )
    parser.add_argument(
        "--config-setup",
        action="store_true",
        default=False,
        help="Use a local environment file to setup access keys and workspace ids",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        metavar="ENVIRONMENT FILE",
        help="path to your environment file",
        default=None,
    )
    parser.add_argument(
        "--workspace",
        type=str,
        metavar="WORKSPACE ID",
        help="your workspace id",
        default=None,
    )
    parser.add_argument(
        "--accesskey",
        type=str,
        metavar="Your Bonsai workspace access-key",
        help="your bonsai workspace access key",
        default=None,
    )
    parser.add_argument(
        "--iteration-limit",
        type=int,
        metavar="EPISODE_ITERATIONS",
        help="Episode iteration limit when running local test.",
        default=200,
    )

    args, _ = parser.parse_known_args()
    logging.basicConfig(level=args.log_level.upper())
    loop = asyncio.get_event_loop()

    set_env(
        config_setup=args.config_setup,
        env_file=args.env_file,
        workspace=args.workspace,
        accesskey=args.accesskey,
    )

    _LOGGER.info("Creating Simulator Session and starting run.")
    sim_session = SimulatorSession()
    try:
        loop.run_until_complete(sim_session.run_loop())
    except KeyboardInterrupt:
        _LOGGER.warning("Stopping Run.")
    except Exception as exc:
        _LOGGER.warning("Stopping Run unexpectedly: %s", exc)
    finally:
        loop.run_until_complete(sim_session.close_session())
    loop.close()
