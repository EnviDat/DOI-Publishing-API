"""Utils that use RemoteCKAN to call actions from CKAN API."""

import logging

import requests
from ckanapi import NotAuthorized, NotFound, RemoteCKAN, ValidationError
from fastapi import HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def ckan_call_action_authorized(
    authorization: str, action: str, data: dict | None = None
):
    """Returns response from authorized calls to CKAN API actions
    on EnviDat CKAN instance.

    Authorization is required.
    NOTE: some CKAN API actions do not require authorization and will still return a
    response even if authorization invalid!
    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        authorization (str): authorization token
        action (str): the CKAN action name, for example 'package_create'
        data (dict): the dict to pass to the action, default is None
    """
    try:
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        if data:
            response = ckan.call_action(action, data)
        else:
            response = ckan.call_action(action)
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404, detail="Not found") from e
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403, detail="Not authorized") from e
    except ValidationError as e:
        # log.exception(e)
        raise HTTPException(status_code=500, detail=f"ValidationError: {e}") from e
    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502, detail="Connection error") from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=500, detail="Error, check logs") from e

    return response


def ckan_call_action_return_exception(
    authorization: str, action: str, data: dict | None = None
):
    """Simplified function that returns dictionary with success Boolean and result
     response from authorized calls to CKAN API actions on EnviDat CKAN instance.

    NOTE: Errors are returned in dictionary rather than raising HTTPException!

    Authorization is required.
    NOTE: Some CKAN API actions do not require authorization and will still return a
    response even if authorization invalid!

    Args:
        authorization (str): authorization token
        action (str): the CKAN action name, for example 'package_create'
        data (dict): the dict to pass to the action, default is None
    """
    try:
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        if data:
            response = ckan.call_action(action, data)
        else:
            response = ckan.call_action(action)
    except Exception as e:
        return {"success": False, "result": e}

    return {"success": True, "result": response}


def ckan_call_action(action: str, data: dict | None = None):
    """Returns response from (unauthorized) calls to public CKAN API actions
    on EnviDat CKAN instance.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        action (str): the CKAN action name, for example 'package_show'
        data (dict): the dict to pass to the action, default is None
    """
    try:
        ckan = RemoteCKAN(settings.API_URL)
        if data:
            response = ckan.call_action(action, data)
        else:
            response = ckan.call_action(action)
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404, detail="Not found") from e
    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502, detail="Connection error") from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=500, detail="Error, check logs") from e

    return response


def ckan_package_show(package_id: str, authorization: str):
    """Return CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        package_id (str): CKAN package id or name
        authorization (str): authorization token
    """
    return ckan_call_action_authorized(
        authorization, "package_show", {"id": package_id}
    )


def ckan_package_patch(package_id: str, data: dict, authorization: str):
    """Patch a CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        package_id (str): CKAN package id or name
        data (dict): the dict with data used to update the CKAN package
        authorization (str): authorization token
    """
    update_data = {"id": package_id, **data}
    return ckan_call_action_authorized(authorization, "package_patch", update_data)


def ckan_package_create(data: dict, authorization: str):
    """Create a CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        data (dict): the dict with data used to create the CKAN package
        authorization (str): authorization token
    """
    return ckan_call_action_authorized(authorization, "package_create", data)


def ckan_current_package_list_with_resources(authorization: str):
    """Return all current CKAN packages with resources.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        authorization (str): authorization token
    """
    return ckan_call_action_authorized(
        authorization, "current_package_list_with_resources", {"limit": "100000"}
    )
