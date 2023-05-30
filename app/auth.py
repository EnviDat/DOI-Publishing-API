"""Validate authorization header and get user details."""

import logging
from typing import Annotated

import ckanapi
from fastapi import Depends, Header, HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def get_user(authorization: Annotated[str | None, Header()] = None):
    """Standard CKAN user."""
    if not settings.DEBUG and not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401, detail="No Authorization header present")

    log.warning(settings.DEBUG)
    log.warning(type(settings.DEBUG))

    log.debug("Authorization header extracted from request headers")

    if settings.DEBUG:
        user_info = {
            "id": "334cee1e-6afa-4639-88a2-f980e6ff42c3",
            "name": "admin",
            "display_name": "EnviDat Admin",
            "email": "envidat@wsl.ch",
            "sysadmin": True,
        }
    else:
        ckan = ckanapi.RemoteCKAN(settings.API_URL, apikey=authorization)
        user_info = ckan.call_action("user_show")

    return user_info


def get_admin(user_info=Depends(get_user)):
    """Admin CKAN user."""
    # Determine if is an admin
    admin = user_info.get("sysadmin", False)

    if not admin:
        log.error(f"User {user_info} is not an admin")
        raise HTTPException(status_code=401, detail=f"User {user_info} is not an admin")

    return user_info
