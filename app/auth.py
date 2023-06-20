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

    log.debug("Authorization header extracted from request headers")

    if settings.DEBUG:
        user_info = {
            "id": settings.DEBUG_USER_ID,
            "name": "admin",
            "display_name": "Admin (Debug)",
            "email": settings.DEBUG_USER_EMAIL,
            "sysadmin": True,
        }
    else:
        try:
            ckan = ckanapi.RemoteCKAN(settings.API_URL, apikey=authorization)
            user_info = ckan.call_action("user_show")
        except ckanapi.errors.NotFound as e:
            raise HTTPException(status_code=404, detail="User not found") from e
        except Exception as e:
            log.error(e)
            raise HTTPException(
                status_code=500, detail="Could not authenticate user"
            ) from e

    return user_info


def get_admin(user_info=Depends(get_user)):
    """Admin CKAN user."""
    # Determine if is an admin
    admin = user_info.get("sysadmin", False)

    if not admin:
        log.error(f"User {user_info} is not an admin")
        raise HTTPException(status_code=401, detail=f"User {user_info} is not an admin")

    return user_info


def get_token(authorization: Annotated[str | None, Header()] = None):
    """Get Authorization header token."""
    return authorization
