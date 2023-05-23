"""Validate authorization header and get user details."""

import logging

import ckanapi
from fastapi import Header, HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def get_user(authorization: str = Header(None)):
    """Standard CKAN user."""
    if not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401, detail="No Authorization header present")

    if settings.DEBUG:
        user_info = {
            "id": "334cee1e-6afa-4639-88a2-f980e6ff42c3",
            "name": "admin",
            "sysadmin": True,
        }
    else:
        ckan = ckanapi.RemoteCKAN(settings.API_URL)
        user_info = ckan.call_action("user_show", api_key=authorization)

    return user_info


def get_admin():
    """Admin CKAN user."""
    user_info = get_user()

    # Determine if is an admin
    admin = user_info.get("sysadmin", False)

    if not admin:
        log.error(f"User {user_info} is not an admin")
        raise HTTPException(status_code=401, detail=f"User {user_info} is not an admin")

    return user_info
