"""Utils module for DOI Publishing API, for debugging."""

import logging
import os
from pathlib import Path
from typing import NoReturn, Union

log = logging.getLogger(__name__)


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


def load_dotenv_if_not_docker(
    env_file: Union[Path, str] = Path(__file__).parent.parent / "secret" / "debug.env",
    force=False,
) -> NoReturn:
    """Load secret .env variables from repo for debugging.

    Args:
        env_file (Union[Path, str]): String or Path like object pointer to
            secret dot env file to read.
            Defaults to './secret/debug.env' from the repo root.
        force (bool): Skip checking for docker and run anyway.
    """
    if bool(os.getenv("IS_DOCKER", default=False)) is True:
        return
    if not force and _is_docker():
        return

    try:
        from dotenv import load_dotenv
    except ImportError as e:
        log.error(
            """
            Unable to import dotenv.
            Note: The logger should be invoked after reading the dotenv file
            so that the debug level is by the environment.

            Is python-dotenv installed?
            Try installing this package using pip install envidat[dotenv].
            """
        )
        log.error(e)

    secret_env = Path(env_file)
    if not secret_env.is_file():
        log.error(
            f"""
            Attempted to import dotenv, but the file does not exist: {secret_env}
            Note: The logger should be invoked after reading the dotenv file
            so that the debug level is by the environment.
            """
        )
    else:
        try:
            load_dotenv(secret_env)
        except Exception as e:
            log.error(e)
            log.error(f"Failed to load dotenv file: {secret_env}")
