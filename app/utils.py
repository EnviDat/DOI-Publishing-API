"""Utils module for DOI Publishing API, for debugging."""

import logging
import os
import sys
from pathlib import Path
from typing import NoReturn, Union

log = logging.getLogger(__name__)


def _debugger_is_active() -> bool:
    """Check to see if running in debug mode.

    Returns:
    -------
        bool: if a debug trace is present or not.
    """
    gettrace = getattr(sys, "gettrace", lambda: None)
    return gettrace() is not None


def _is_docker() -> bool:
    """Check to see if running in a docker container.

    Returns:
        bool: if a docker related components present on filesystem.
    """
    path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(path)
        and any("docker" in line for line in open(path))
    )


def load_dotenv_if_in_debug_mode(
    env_file: Union[Path, str] = Path(__file__).parent.parent / "debug.env"
) -> NoReturn:
    """Load secret .env variables from repo for debugging.

    Args:
        env_file (Union[Path, str]): String or Path like object pointer to
            secret dot env file to read.
            Defaults to file 'debug.env' in repo root.
    """
    if not _debugger_is_active():
        return

    is_docker_from_env = os.getenv("IS_DOCKER", default=False)
    if _is_docker() or is_docker_from_env:
        return

    try:
        from dotenv import load_dotenv
    except ImportError as e:
        log.error(
            """
            Unable to import dotenv.
            Note: The logger should be invoked after reading the dotenv file
            so that the debug level is by the environment.
            """
        )
        log.error(e)
        raise ImportError(
            """
            Unable to import dotenv, is python-dotenv installed?
            Try installing this package using pip install envidat[dotenv].
            """
        ) from e

    secret_env = Path(env_file)
    if not secret_env.is_file():
        log.error(
            """
            Attempted to import dotenv, but the file does not exist.
            Note: The logger should be invoked after reading the dotenv file
            so that the debug level is by the environment.
            """
        )
        raise FileNotFoundError(
            f"Attempted to import dotenv, but the file does not exist: {env_file}"
        ) from None
    else:
        load_dotenv(secret_env)
