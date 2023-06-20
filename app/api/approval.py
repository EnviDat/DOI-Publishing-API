"""Endpoints to trigger emails."""

import logging

import ckanapi
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import get_token, get_user
from app.config import settings
from app.logic.mail import request_approval_email

log = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["approval"])


@router.get("/request")
async def request_publish_approval(
    package_id: str,
    update: bool = False,
    user=Depends(get_user),
    auth_token=Depends(get_token),
):
    """Request approval to publish."""
    # Send email to admin
    await request_approval_email(package_id=package_id, user_email=user.email)

    # FIXME Requires testing
    log.debug("Initialising CKAN connection")
    ckan = ckanapi.RemoteCKAN(settings.API_URL, apikey=auth_token)

    log.debug(
        f"Updating package {id} to publication_status="
        f"{'updated' if update else 'pub_pending'}"
    )
    ckan.call_action(
        "package_update",
        {"publication_status": "updated" if update else "pub_pending"},
    )
    return JSONResponse(status_code=200, content={"success": True})
