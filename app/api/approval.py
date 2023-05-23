"""Endpoints to trigger emails."""

import logging

import ckanapi
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.config import settings
from app.logic.mail import approval_granted_email, request_approval_email

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/approval",
    tags=["approval"],
)


@router.get("/request")
async def request_publish_approval(package_id: str, authorization: str = Header(None)):
    """Request approval to publish."""
    # Send email to admin
    request_approval_email()

    # Requires testing
    log.debug("Initialising CKAN connection")
    ckan = ckanapi.RemoteCKAN(settings.API_URL)
    log.debug(f"Updating package {id} to publication_status=pub_pending")
    ckan.call_action(
        "package_update", {"publication_status": "pub_pending"}, api_key=authorization
    )
    return JSONResponse(status_code=200, content={"success": True})


@router.get("/approve")
async def approve_publishing(package_id: str, authorization: str = Header(None)):
    """Request approval to publish."""
    # Requires testing
    log.debug("Initialising CKAN connection")
    ckan = ckanapi.RemoteCKAN(settings.API_URL)
    log.debug(f"Updating package {id} to publication_status=approved")
    ckan.call_action(
        "package_update", {"publication_status": "approved"}, api_key=authorization
    )

    log.debug("Attempting update via Datacite API")
    # # Call Datacite update handler datacite.py
    # if datacite_error:
    #     HTTPException(
    #         status_code=409,
    #         detail=f"Error with datacite update: {datacite_error}"
    #     )

    # Send email to user
    approval_granted_email()

    return JSONResponse(status_code=200, content={"success": True})
