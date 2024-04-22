"""Config file for TortoiseORM and database init."""

import logging

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from tortoise import Tortoise

from app.config import config_app

log = logging.getLogger(__name__)

TORTOISE_ORM = {
    "connections": {"default": config_app.DB_URI},
    "apps": {
        config_app.__NAME__: {
            "models": [
                "app.models.doi",
            ],
            "default_connection": "default",
        },
    },
    "routers": [],
    "use_tz": False,
    "timezone": "UTC",
}


def init_db(app: FastAPI) -> None:
    """Register and create database connection."""
    log.debug(f"Connecting to DB...")
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        add_exception_handlers=True,
    )

async def close_db() -> None:
    """Close database connections."""
    log.debug(f"Closing connections to DB")
    await Tortoise.close_connections()
