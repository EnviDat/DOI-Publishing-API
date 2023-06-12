"""Validate authorization header and get user details."""

from typing import Annotated

import requests
from ckanapi import RemoteCKAN, NotFound
from fastapi import Depends, Header, HTTPException, Cookie
from app.config import settings

import logging

log = logging.getLogger(__name__)


# TODO review exception formatting


# TODO review if more generic exceptions should be returned
#  (for example status 500, detail User not Found)
# TODO review if auth method should use cookie or authorization header,
#  this version uses authorization in header
def authorize_user(user_id: str,
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

    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502,
                            detail="Connection error")

    return user


# TODO test with admin user
# TODO review if DEBUG needed
# TODO review if more generic exceptions should be returned
#  (for example status 500, detail User not Found)
# TODO review if auth method should use cookie or authorization header,
#  this version uses cookie which will only work on same website,
#  NOTE: cookie may not work when sending to an external site
# def get_user(user_id: str = None,
#              ckan: Annotated[str | None, Cookie()] = None):
#     """Authorize and return CKAN user."""
#     # if not authorization:
#     #     log.error("No Authorization header present")
#     #     raise HTTPException(status_code=401,
#     #                         detail="No Authorization header present")
#
#     try:
#         ckan = RemoteCKAN(settings.API_URL, apikey=ckan)
#         user = ckan.call_action("user_show", {'id': user_id})
#
#         # Check if user has email property,
#         # this indicates the user is authorized.
#         # If email not present then raise HTTPException.
#         if not user.get('email'):
#             raise HTTPException(
#             status_code=403, detail="User not authorized")
#
#     except NotFound as e:
#         log.exception(e)
#         raise HTTPException(status_code=404,
#                             detail="User not found")
#
#     return user


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


# TODO possibly implement more generic HTTPException message
def authorize_admin(authorization: Annotated[str | None, Header()] = None):
    """Authorize and return admin CKAN user."""

    try:
        admin_user_id = settings.ADMIN_USER_ID
    except KeyError:
        raise HTTPException(status_code=500, detail="Internal server error")

    user = authorize_user(admin_user_id, authorization)

    is_sysadmin = user.get("sysadmin", False)
    if not is_sysadmin:
        log.error(f"User {user} is not an admin")
        raise HTTPException(status_code=401,
                            detail="User not authorized")

    return user


# TODO review
def get_admin(user=Depends(authorize_user)):
    """Authorize and return admin CKAN user."""

    admin = user.get("sysadmin", False)

    if not admin:
        log.error(f"User {user} is not an admin")
        raise HTTPException(status_code=401,
                            detail="User not authorized")

    return user


def get_token(authorization: Annotated[str | None, Header()] = None):
    """Get Authorization header token."""
    return authorization
