"""Helper functions for runnings sims."""
from __future__ import annotations

import logging
import os
from dotenv import load_dotenv, set_key

_LOGGER = logging.getLogger(__name__)


def set_env(
    config_setup: bool = False,
    env_file: str | bool = ".env",
    workspace: str = None,
    accesskey: str = None,
):
    """Set the environment variables and check that so that BonsaiClientConfig can read them.

    Check for accesskey and workspace id in system variables.
    Three scenarios
    1. workspace and accesskey provided by CLI args
    2. dotenv provided
    3. system variables
    do 1 if provided, use 2 if provided; ow use 3; if no sys vars or dotenv, fail

    Parameters
    ----------
    config_setup: bool, optional
        if enabled then uses a local `.env` file to find sim workspace id and access_key
    env_file: str, optional
        if config_setup True, then where the environment variable for lookup exists
    workspace: str, optional
        optional flag from CLI for workspace to override
    accesskey: str, optional
        optional flag from CLI for accesskey to override

    """
    if workspace and accesskey:
        os.environ["SIM_WORKSPACE"] = workspace
        os.environ["SIM_ACCESS_KEY"] = accesskey

    if env_file or config_setup:
        if not isinstance(env_file, str):
            env_file = ".env"
        _LOGGER.info(
            f"No system variables for workspace-id or access-key found, checking in env-file at {env_file}"
        )
        env_setup(env_file)

    try:
        assert os.environ["SIM_WORKSPACE"]
        assert os.environ["SIM_ACCESS_KEY"]
    except AssertionError as exc:
        raise IndexError(
            "Workspace or access key not set or found. Use --config-setup for help setting up."
        ) from exc


def env_setup(env_file: str = ".env") -> None:  # type: ignore
    """Load the .env file and store in environment, if empty no problem yet.

    Get both workspace and access key and check if the file exists, if not create it.
    If workspace is not in env, ask for workspace input and store in env file.
    If accesskey is not in env, ask for accesskey input and store in env file.

    Load the env file into environment.
    """
    load_dotenv(dotenv_path=env_file, verbose=True, override=True)

    workspace = os.getenv("SIM_WORKSPACE")
    access_key = os.getenv("SIM_ACCESS_KEY")

    env_file_exists = os.path.exists(env_file)
    if not env_file_exists:
        open(env_file, "a").close()

    if not workspace:
        workspace = input("Please enter your workspace id: ")
        set_key(env_file, "SIM_WORKSPACE", workspace)  # type: ignore
    if not access_key:
        access_key = input("Please enter your access key: ")
        set_key(env_file, "SIM_ACCESS_KEY", access_key)  # type: ignore

    load_dotenv(dotenv_path=env_file, verbose=True, override=True)
