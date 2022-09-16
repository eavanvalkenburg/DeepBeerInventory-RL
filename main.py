# from __future__ import print_function
# from sim.beer_game import BeerGame
# from sim.utilities import *
# import numpy as np

# # from clGeneralParameters import generalParameters
# import random
# from sim.config import get_config, update_config

# config = None

# # def main(config, beerGame):
# def main(config):
#     random.seed(10)

#     # prepare loggers and directories
#     prepare_dirs_and_logger(config)
#     config = update_config(config)
#     # save the current configuration of the problem in a json file
#     save_config(config)

#     # get the address of data
#     # if config.observation_data:
#     #     adsr = "data/demandTr-obs-"
#     # elif config.demandDistribution == 3:
#     #     if config.scaled:
#     #         adsr = "data/basket_data/scaled"
#     #     else:
#     #         adsr = "data/basket_data"
#     # elif config.demandDistribution == 4:
#     #     if config.scaled:
#     #         adsr = "data/forecast_data/scaled"
#     #     else:
#     #         adsr = "data/forecast_data"
#     # else:
#     #     adsr = "data/demandTr"

#     # load demands
#     # demandTr = np.load('demandTr'+str(config.demandDistribution)+'-'+str(config.demandUp)+'.npy')
#     # if config.demandDistribution == 0:
#     #     direc = os.path.realpath(
#     #         adsr + str(config.demandDistribution) + "-" + str(config.demandUp) + ".npy"
#     #     )
#     #     if not os.path.exists(direc):
#     #         direc = os.path.realpath(
#     #             adsr
#     #             + str(config.demandDistribution)
#     #             + "-"
#     #             + str(config.demandUp)
#     #             + ".npy"
#     #         )
#     # elif config.demandDistribution == 1:
#     #     direc = os.path.realpath(
#     #         adsr
#     #         + str(config.demandDistribution)
#     #         + "-"
#     #         + str(int(config.demandMu))
#     #         + "-"
#     #         + str(int(config.demandSigma))
#     #         + ".npy"
#     #     )
#     # elif config.demandDistribution == 2:
#     #     direc = os.path.realpath(adsr + str(config.demandDistribution) + ".npy")
#     # elif config.demandDistribution == 3:
#     #     direc = os.path.realpath(adsr + "/demandTr-" + str(config.data_id) + ".npy")
#     # elif config.demandDistribution == 4:
#     #     direc = os.path.realpath(adsr + "/demandTr-" + str(config.data_id) + ".npy")

#     # initilize an instance of Beergame
#     beer_game = BeerGame(config)

#     # train the specified number of games
#     if config.maxEpisodesTrain:
#         for i in range(0, config.maxEpisodesTrain):
#             beer_game.playGame(demandTr[i % demand_len], "train")
#             # get the test results
#             # if (np.mod(beer_game.curGame, config.testInterval) == 0) and (
#             #     beer_game.curGame > 500
#             # ):
#             # beer_game.doTestMid(demandTs[0 : config.testRepeatMid])
#     else:
#         beer_game.playGame(demandTr[0], "train")

#     # do the last test on the middle test data set.
#     beer_game.doTestMid(demandTs[0 : config.testRepeatMid])
#     if config.demandDistribution == 3:
#         beer_game.doTestMid(demandVl[0 : config.testRepeatMid])


# if __name__ == "__main__":
#     # load parameters
#     config, unparsed = get_config()

#     # run main
#     main(config)


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
    # TestSession,
)

_LOGGER = logging.getLogger(__name__)


# async def test_policies(args):
#     """Run the test policies."""
#     session = None
#     if args.test_random:
#         test_session = TestSession(
#             num_iterations=args.iteration_limit,
#             policy=random_policy,
#             policy_name="random",
#         )
#     elif args.test_loop:
#         test_session = TestSession(
#             num_iterations=args.iteration_limit,
#             policy=loop_policy,
#             policy_name="loop",
#         )
#     elif args.test_exported:
#         url = f"http://localhost:{args.test_exported}"
#         _LOGGER.info(f"Connecting to exported brain running at {url}...")
#         session = aiohttp.ClientSession()
#         trained_brain_policy = partial(
#             brain_policy, exported_brain_url=url, session=session
#         )
#         test_session = TestSession(
#             num_iterations=args.iteration_limit,
#             policy=trained_brain_policy,
#             policy_name="exported",
#         )
#     try:
#         await test_session.run()
#     finally:
#         if session:
#             await session.close()


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
