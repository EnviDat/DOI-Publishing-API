"""Config file for TortoiseORM and database init."""

import logging

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.config import settings

log = logging.getLogger(__name__)

TORTOISE_ORM = {
    "connections": {"default": settings.DB_URI},
    "apps": {
        settings.APP_NAME: {
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
    log.debug(f"Connecting to DB: {settings.DB_URI}")
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        add_exception_handlers=True,
    )
