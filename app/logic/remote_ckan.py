"""Utils that use RemoteCKAN to call actions from CKAN API."""

import logging

import requests
from ckanapi import NotAuthorized, NotFound, RemoteCKAN, ValidationError
from fastapi import HTTPException

from app.config import settings

log = logging.getLogger(__name__)


def get_ckan(api_token: str):
    """Get CKAN session once, to re-use the connection."""
    return RemoteCKAN(settings.CKAN_API_URL, apikey=api_token)


def ckan_call_action_handle_errors(
    ckan: RemoteCKAN, action: str, data: dict | None = None
):
    """Wrapper for CKAN actions, handling errors.

    An authorised RemoteCKAN instance is required.
    NOTE: some CKAN API actions do not require authorization and will still return a
    response even if authorization invalid!
    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        ckan (RemoteCKAN): authorised RemoteCKAN session.
        action (str): the CKAN action name, for example 'package_create'
        data (dict): the dict to pass to the action, default is None
    """
    try:
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
        log.exception(e)
        raise HTTPException(status_code=500, detail=f"ValidationError: {e}") from e
    except requests.exceptions.ConnectionError as e:
        log.exception(e)
        raise HTTPException(status_code=502, detail="Connection error") from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=500, detail="Error, check logs") from e

    return response


def ckan_call_action_return_exception(
    ckan: RemoteCKAN, action: str, data: dict | None = None
):
    """Handle exceptions from ckanapi while calling ckan action.

    Simplified function that returns dictionary with success Boolean and result
     response from authorized calls to CKAN API actions on EnviDat CKAN instance.

    NOTE: Errors are returned in dictionary rather than raising HTTPException!

    Authorization is required.
    NOTE: Some CKAN API actions do not require authorization and will still return a
    response even if authorization invalid!

    Args:
        ckan (RemoteCKAN): authorised RemoteCKAN session.
        action (str): the CKAN action name, for example 'package_create'
        data (dict): the dict to pass to the action, default is None
    """
    try:
        if data:
            response = ckan.call_action(action, data)
        else:
            response = ckan.call_action(action)
    except Exception as e:
        return {"success": False, "result": e}

    return {"success": True, "result": response}


def ckan_package_show(package_id: str, ckan: RemoteCKAN):
    """Return CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        package_id (str): CKAN package id or name
        ckan (RemoteCKAN): authorised RemoteCKAN session.
    """
    return ckan_call_action_handle_errors(ckan, "package_show", {"id": package_id})


def ckan_package_patch(package_id: str, data: dict, ckan: RemoteCKAN):
    """Patch a CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        package_id (str): CKAN package id or name
        data (dict): the dict with data used to update the CKAN package
        ckan (RemoteCKAN): authorised RemoteCKAN session.
    """
    update_data = {"id": package_id, **data}
    return ckan_call_action_handle_errors(ckan, "package_patch", update_data)


def ckan_package_create(data: dict, ckan: RemoteCKAN):
    """Create a CKAN package.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        data (dict): the dict with data used to create the CKAN package
        ckan (RemoteCKAN): authorised RemoteCKAN session.
    """
    return ckan_call_action_handle_errors(ckan, "package_create", data)


def ckan_current_package_list_with_resources(ckan: RemoteCKAN):
    """Return all current CKAN packages with resources.

    If CKAN API call fails then logs error and raises HTTPException.

    Args:
        ckan (RemoteCKAN): authorised RemoteCKAN session.
    """
    return ckan_call_action_handle_errors(
        ckan, "current_package_list_with_resources", {"limit": "100000"}
    )
