"""Endpoints to trigger emails."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import get_admin, get_token, get_user
from app.logic.mail import request_approval_email
from app.logic.remote_ckan import ckan_package_patch

log = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["approval"])


@router.get("/request")
async def request_publish_approval(
    package_id: str,
    request: Request,
    user=Depends(get_user),
    auth_token=Depends(get_token),
    is_update: bool = False,
):
    """Request approval to publish."""
    if not (user_name := user.get("display_name", None)):
        raise HTTPException(status_code=500, detail="Username not extracted")
    if not (user_email := user.get("email", None)):
        raise HTTPException(status_code=500, detail="User email not extracted")

    await request_approval_email(
        package_id=package_id,
        user_name=user_name,
        user_email=user_email,
        approval_url=str(request.base_url).rstrip("/"),
        is_update=is_update,
    )

    status = "approved" if is_update else "pub_pending"
    log.debug(f"Updating package {package_id} to publication_state={status}")
    response = ckan_package_patch(package_id, {"publication_state": status}, auth_token)
    log.debug(f"CKAN response: {response}")
    return JSONResponse(status_code=200, content={"success": True})


@router.get("/accept")
async def accept_publish_request(
    package_id: str,
    user=Depends(get_admin),
    auth_token=Depends(get_token),
):
    """Admin endpoint to approve a publication request."""
    log.debug(f"Updating package {package_id} to publication_state=published")
    ckan_package_patch(package_id, {"publication_state": "published"}, auth_token)
    return JSONResponse(status_code=200, content={"success": True})
