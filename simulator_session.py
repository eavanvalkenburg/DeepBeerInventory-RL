"""
MSFT Bonsai SDK3 Template for Simulator Integration using Python.

Copyright 2021 Microsoft

Usage:
  For registering simulator with the Bonsai service for training:
    python simulator_integration.py
    Then connect your registered simulator to a Brain via UI, or using the CLI: `bonsai simulator unmanaged connect -b <brain-name> -a <train-or-assess> -c BalancePole --simulator-name TrafficSchool
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Mapping
from typing import Any

from azure.core.exceptions import HttpResponseError
from microsoft_bonsai_api.simulator.client import BonsaiClientAsync, BonsaiClientConfig
from microsoft_bonsai_api.simulator.generated.models import (
    Event,
    EventType,
    SimulatorInterface,
    SimulatorSessionResponse,
    SimulatorState,
)

from sim.beer_game import BeerGame

_LOGGER = logging.getLogger(__name__)

default_config: Mapping[str, int] = {}


class TemplateSimulatorSession:
    """Template simulator session."""

    def __init__(self, env_name: str = "BeerGame") -> None:
        """Create Simulator Interface with the Bonsai Platform."""
        self.simulator = BeerGame()
        self.env_name = env_name

    def get_state(self) -> Mapping[str, Any]:
        """Extract current states from the simulator.

        Returns
        -------
        Dict[str, float]
            Returns float of current values from the simulator
        """
        state = self.simulator.state.copy()
        _LOGGER.debug("Current state: %s", state)
        return state

    def halted(self) -> bool:
        """Halt current episode. Note, this should only return True if the simulator has reached an unexpected state.

        Returns
        -------
        bool
            Whether to terminate current episode
        """
        return False

    def episode_start(self, config: dict[str, Any] = default_config) -> None:
        """
        Initialize simulator environment using scenario paramters from inkling. Note, `simulator.reset()` initializes the simulator parameters for initial positions and velocities of the cart and pole using a random sampler. See the source for details.

        Parameters
        ----------
        config : Dict, optional. The following keys are supported:
        """
        config["agent_types"] = ["bonsai", "basestock", "basestock", "basestock"]
        if "agent_type1" in config:
            config["agent_types"][0] = config.pop("agent_type1")
        if "agent_type2" in config:
            config["agent_types"][1] = config.pop("agent_type2")
        if "agent_type3" in config:
            config["agent_types"][2] = config.pop("agent_type3")
        if "agent_type4" in config:
            config["agent_types"][3] = config.pop("agent_type4")
        _LOGGER.debug("Starting episode with config: %s", config)
        self.simulator.reset(**config)

    def episode_step(self, action: Mapping[str, int]) -> None:
        """Step through the environment for a single iteration.

        Parameters
        ----------
        action : Dict
            An action to take to modulate environment.
        """
        self.simulator.step(int(action["order"]))


class SimulatorSession:
    """Simulator session object that allows for async execution."""

    def __init__(self):
        """Create the SimulatorSession for the simulator connection."""
        self.registered_session: SimulatorSessionResponse | None = None
        self.sequence_id: int = 0

        # Load json file as simulator integration config type file
        with open("sim//beergame.json") as file:
            self.interface = json.load(file)

        # Configure sim & client to interact with Bonsai service
        self.sim = TemplateSimulatorSession()
        self.config_client = BonsaiClientConfig()
        self.client = BonsaiClientAsync(self.config_client)

        # Create simulator session and init sequence id
        self.registration_info = SimulatorInterface(
            name=self.sim.env_name,
            timeout=self.interface["timeout"],
            simulator_context=self.config_client.simulator_context,
            description=self.interface["description"],
        )

    async def create_session(self) -> None:
        """Create a new Simulator Session and store the session and sequenceId."""
        _LOGGER.info(
            "Config: %s, %s",
            self.config_client.server,
            self.config_client.workspace,
        )
        try:
            self.registered_session = await self.client.session.create(
                workspace_name=self.config_client.workspace,
                body=self.registration_info,
            )
        except HttpResponseError as ex:
            _LOGGER.warning(
                "HttpResponseError in Registering session: StatusCode: %s, Error: %s, Exception: %s",
                ex.status_code,
                ex.error.message,  # type: ignore
                ex,
            )
            raise ex
        except Exception as ex:
            _LOGGER.warning(
                "UnExpected error: %s, Most likely, it's some network connectivity issue, make sure you are able to reach bonsai platform from your network.",
                ex,
            )
            raise ex
        self.sequence_id = 1
        _LOGGER.info("Registered simulator. %s", self.registered_session.session_id)

    async def close_session(self) -> None:
        """Close the session."""
        if self.registered_session:
            await self.client.session.delete(
                workspace_name=self.config_client.workspace,
                session_id=self.registered_session.session_id,
            )
            _LOGGER.info("Unregistered simulator.")
        await self.client.close()

    async def run_loop(self) -> None:
        """Run the main loop waiting for actions from Bonsai.

        Proceed to the next event by calling the advance function and passing the simulation state
        resulting from the previous event. Note that the sim must always be able to return a valid
        structure from get_state, including the first time advance is called, before an EpisodeStart
        message has been received.

        """
        while True:
            if not self.registered_session:
                await self.create_session()
            try:
                event = await self.client.session.advance(
                    workspace_name=self.config_client.workspace,
                    session_id=self.registered_session.session_id,  # type: ignore
                    body=SimulatorState(
                        sequence_id=self.sequence_id,
                        state=self.sim.get_state(),
                        halted=self.sim.halted(),
                    ),
                )
            except HttpResponseError as ex:
                # This can happen in network connectivity issue, though SDK has retry logic, but even after that request may fail,
                # if your network has some issue, or sim session at platform is going away..
                # So let's re-register sim-session and get a new session and continue iterating. :-)
                _LOGGER.warning(
                    "HttpResponseError in Advance: StatusCode: %s, Error: %s, Exception: %s",
                    ex.status_code,
                    ex.error.message,  # type: ignore
                    ex,
                )
                self.registered_session = None
            except Exception as err:
                # Ideally this shouldn't happen, but for very long-running sims It can happen with various reasons, let's re-register sim & Move on.
                # If possible try to notify Bonsai team to see, if this is platform issue and can be fixed.
                _LOGGER.warning("Unexpected error in Advance: %s", err)
                self.registered_session = None
            else:
                await self._handle_bonsai_event(event)

    async def _handle_bonsai_event(self, event: Event) -> None:
        """Run the inner loop with the event."""
        _LOGGER.debug("[%s] Last Event: %s", time.strftime("%H:%M:%S"), event.type)
        self.sequence_id = event.sequence_id
        if event.type == EventType.EPISODE_STEP:
            _LOGGER.debug("Action: %s", event.episode_step.action)
            self.sim.episode_step(event.episode_step.action)
            return

        if event.type == EventType.EPISODE_START:
            _LOGGER.info("Starting episode with config: %s", event.episode_start.config)
            self.sim.episode_start(event.episode_start.config)
            return

        if event.type == EventType.EPISODE_FINISH:
            _LOGGER.info("Episode Finishing...")
            return

        if event.type == EventType.IDLE:
            _LOGGER.debug("Idling...")
            await asyncio.sleep(event.idle.callback_time)
            return

        if event.type == EventType.UNREGISTER:
            _LOGGER.warning(
                "Simulator Session unregistered by platform because '%s', Registering again!",
                event.unregister.details,
            )
            self.registered_session = None
            return
