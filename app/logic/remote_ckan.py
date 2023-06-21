"""Utils that use RemoteCKAN to call actions from CKAN API."""

# Setup logging
import logging

import requests
from ckanapi import NotAuthorized, NotFound, RemoteCKAN
from fastapi import HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def ckan_package_show(package_id: str, authorization: str):
    """Return CKAN package.

    In case of some errors raises HTTPException.
    """
    try:
        ckan = RemoteCKAN(settings.CKAN_API_URL, apikey=authorization)
        package = ckan.call_action("package_show", {"id": package_id})
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404, detail="Package not found") from e
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403, detail="User not authorized") from e
    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502, detail="Connection error") from e

    return package


def ckan_package_patch(
    package_id: str,
    data: dict,
    authorization: str,
):
    """Patch a CKAN package.

    Authorization header required to update package.
    In case of some errors raises HTTPException.
    """
    try:
        data_dict = {"id": package_id, **data}
        ckan = RemoteCKAN(settings.CKAN_API_URL, apikey=authorization)
        package = ckan.call_action("package_patch", data_dict)
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404, detail="Package not found") from e
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403, detail="User not authorized") from e
    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502, detail="Connection error") from e

    return package
