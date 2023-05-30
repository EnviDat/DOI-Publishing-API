"""Endpoints to trigger emails."""

import logging

import ckanapi
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.config import settings
from app.logic.mail import request_approval_email

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/approval",
    tags=["approval"],
)


@router.get("/request")
async def request_publish_approval(
    package_id: str, update: bool = False, authorization: str = Header(None)
):
    """Request approval to publish."""
    # Send email to admin
    request_approval_email(package_id="", user_email="")

    # Requires testing
    log.debug("Initialising CKAN connection")
    ckan = ckanapi.RemoteCKAN(settings.API_URL)

    log.debug(
        f"Updating package {id} to publication_status="
        f"{'updated' if update else 'pub_pending'}"
    )
    ckan.call_action(
        "package_update",
        {"publication_status": "updated" if update else "pub_pending"},
        api_key=authorization,
    )
    return JSONResponse(status_code=200, content={"success": True})
