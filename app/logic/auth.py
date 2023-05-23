import logging

import ckanapi

from fastapi import Header

log = logging.getLogger(__name__)


def verify_user(authorization: str = Header(None)):
    if not authorization:
        log.error("Not Authorization header present")
        return

    ckan = ckanapi.RemoteCKAN(settings.API_URL)

    user_info = ckan.call_action(
        "user_show",
        {
            "include_datasets": False,
        },
        api_key=authorization,
    )

    return user_info
