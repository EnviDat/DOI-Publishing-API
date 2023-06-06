"""Validate authorization header and get user details."""

from typing import Annotated

from ckanapi import RemoteCKAN, NotFound
from fastapi import Depends, Header, HTTPException
from app.config import settings

import logging

log = logging.getLogger(__name__)


# TODO review exception formatting

# TODO test with admin user
# TODO review if DEBUG needed
def get_user(user_id: str,
             authorization: Annotated[str | None, Header()] = None):
    """Authorize and return CKAN user."""
    if not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401,
                            detail="No Authorization header present")

    try:
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        user = ckan.call_action("user_show", {'id': user_id})

        # Check if user has email property,
        # this indicates the user is authorized.
        # If email not present then raise HTTPException.
        if not user.get('email'):
            raise HTTPException(status_code=403, detail="User not authorized")

    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404,
                            detail="User not found")

    return user


# TODO revew
# def get_user(authorization: Annotated[str | None, Header()] = None):
#     """Standard CKAN user."""
#     if not settings.DEBUG and not authorization:
#         log.error("No Authorization header present")
#         raise HTTPException(status_code=401,
#         detail="No Authorization header present")
#
#     log.warning(settings.DEBUG)
#     log.warning(type(settings.DEBUG))
#
#     log.debug("Authorization header extracted from request headers")
#
#     if settings.DEBUG:
#         user_info = {
#             "name": "admin",
#             "display_name": "EnviDat Admin",
#             "email": "envidat@wsl.ch",
#             "sysadmin": True,
#         }
#     else:
#         ckan = ckanapi.RemoteCKAN(settings.API_URL, apikey=authorization)
#         user_info = ckan.call_action("user_show")
#
#     return user_info


def get_admin(user=Depends(get_user)):
    """Admin CKAN user."""
    # Determine if is an admin
    admin = user.get("sysadmin", False)

    if not admin:
        log.error(f"User {user} is not an admin")
        raise HTTPException(status_code=401,
                            detail=f"User {user} is not an admin")

    return user


# TODO review
# def get_admin(user_info=Depends(get_user)):
#     """Admin CKAN user."""
#     # Determine if is an admin
#     admin = user_info.get("sysadmin", False)
#
#     if not admin:
#         log.error(f"User {user_info} is not an admin")
#         raise HTTPException(status_code=401,
#                             detail=f"User {user_info} is not an admin")
#
#     return user_info


def get_token(authorization: Annotated[str | None, Header()] = None):
    """Get Authorization header token."""
    return authorization
