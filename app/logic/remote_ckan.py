"""Utils that use RemoteCKAN to call actions from CKAN API."""

from typing import Annotated

from ckanapi import RemoteCKAN, NotFound, NotAuthorized
from fastapi import HTTPException, Header

from app.config import settings

# Setup logging
import logging

log = logging.getLogger(__name__)


# TODO review if authorization should be in header or cookie


def ckan_package_show(
        package_id: str,
        authorization: Annotated[str | None, Header()] = None
):
    """
    Return CKAN package.

    In case of some errors raises HTTPException.
    """

    if not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401,
                            detail="No Authorization header present")

    try:
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        package = ckan.call_action("package_show", {'id': package_id})
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404,
                            detail="Package not found")
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403,
                            detail="User not authorized")

    return package


def ckan_package_patch(
        package_id: str,
        data: dict,
        authorization: Annotated[str | None, Header()] = None
):
    """
    Patch a CKAN package.
    """

    if not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401,
                            detail="No Authorization header present")

    try:
        data_dict = {'id': package_id, **data}
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        package = ckan.call_action("package_patch", data_dict)
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404,
                            detail="Package not found")
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403,
                            detail="User not authorized")

    return package

