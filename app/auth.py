"""Validate authorization header and get user details."""

import logging
from typing import Annotated

from ckanapi import NotFound
from fastapi import Depends, Header, HTTPException

from app.config import settings
from app.logic.remote_ckan import get_ckan

log = logging.getLogger(__name__)


def get_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    """Return a CKAN API instance for a standard user."""
    if not settings.DEBUG and not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401, detail="No Authorization header present")

    log.debug("Authorization header extracted from request headers")

    if settings.DEBUG:
        ckan = None
        user_info = {
            "id": settings.DEBUG_USER_ID,
            "name": "admin",
            "display_name": "Admin (Debug)",
            "email": settings.DEBUG_USER_EMAIL,
            "sysadmin": True,
        }
    else:
        try:
            ckan = get_ckan(authorization)
            user_info = ckan.call_action("user_show")
        except NotFound as e:
            raise HTTPException(status_code=404, detail="User not found") from e
        except Exception as e:
            log.error(e)
            raise HTTPException(
                status_code=500, detail="Could not authenticate user"
            ) from e

    return {"info": user_info, "ckan": ckan}


def get_admin(user=Depends(get_user)) -> dict:
    """Return a CKAN API instance for an admin user."""
    user_info = user.get("info")
    # Determine if is an admin
    admin = user_info.get("sysadmin", False)

    if not admin:
        log.debug(f"Extracting username from user obj: {user}")
        username = user.info.get("name", None)
        log.error(f"Not an admin. User: {username}")
        raise HTTPException(status_code=401, detail=f"Not an admin. User: {username}")

    return user


def get_token(authorization: Annotated[str | None, Header()] = None) -> str:
    """Get Authorization header token."""
    return authorization
