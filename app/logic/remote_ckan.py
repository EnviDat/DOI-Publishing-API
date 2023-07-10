"""Utils that use RemoteCKAN to call actions from CKAN API."""

# Setup logging
import logging

import requests
from ckanapi import NotAuthorized, NotFound, RemoteCKAN
from fastapi import HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def get_ckan(api_token: str):
    """Get CKAN session once, to re-use the connection."""
    return RemoteCKAN(settings.CKAN_API_URL, apikey=api_token)


def ckan_package_show(package_id: str, ckan: RemoteCKAN):
    """Return CKAN package.

    In case of some errors raises HTTPException.
    """
    try:
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


def ckan_package_patch(package_id: str, data: dict, ckan: RemoteCKAN):
    """Patch a CKAN package.

    In case of some errors raises HTTPException.
    """
    try:
        data_dict = {"id": package_id, **data}
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
