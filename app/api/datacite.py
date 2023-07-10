"""DataCite API Router."""

# Setup logging
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

# from app.api.doi import create_doi_draft
from app.auth import get_admin, get_user
from app.config import settings
from app.logic.datacite import (
    DoiErrors,
    DoiSuccess,
    get_error_message,
    publish_datacite,
    reserve_draft_doi_datacite,
    validate_doi,
)
from app.logic.mail import (
    approval_granted_email,
    draft_failed_email,
    request_approval_email,
)
from app.logic.minter import create_db_doi
from app.logic.remote_ckan import ckan_package_patch, ckan_package_show

log = logging.getLogger(__name__)

# TODO test with production
# TODO verify signout
# TODO review HTTPException formatting, possibly use more generic messages

# TODO review implementation of auth and dependencies


# TODO review and remove dependencies if unused
# Setup datacite router
router = APIRouter(
    prefix="/datacite",
    tags=["datacite"]
    # dependencies=[Depends(get_user)]
)


@router.get(
    "/draft",
    name="Reserve draft DOI",
    status_code=201,
    responses={
        201: {
            "model": DoiSuccess,
            "description": "Draft DOI successfully reserved with DataCite",
        },
        422: {"model": DoiErrors},
        500: {"model": DoiErrors},
        502: {"model": DoiErrors},
    },
)
async def reserve_draft_doi(
    package_id: Annotated[
        str, Query(alias="package-id", description="CKAN package id or name")
    ],
    response: Response,
    user=Depends(get_user),
):
    """Generate new DOI from DB and reserve draft DOI in DataCite."""
    user_info = user.get("info")
    ckan = user.get("ckan")

    package = ckan_package_show(package_id, ckan)

    if not (user_name := user_info.get("name", None)):
        log.error("Failure extracting username using Authorization header")
        raise HTTPException(status_code=500, detail="Username not extracted")
    if not (user_email := user_info.get("email", None)):
        log.error("Failure extracting email using Authorization header")
        raise HTTPException(status_code=500, detail="User email not extracted")

    # Create new DOI
    if (doi := await create_db_doi(user_name, package)) is None:
        log.error("Failed creating new DOI in database")
        return HTTPException(status_code=500, detail="New DOI creation failed")

    successful_status_codes = range(200, 300)
    datacite_response = {}
    retry_count = 0

    while retry_count <= settings.DATACITE_RETRIES:

        datacite_response = reserve_draft_doi_datacite(doi)
        log.debug(f"DataCite response: {datacite_response}")

        if datacite_response.get("status_code") in successful_status_codes:
            log.debug(
                "DataCite publish successful, "
                f"patching CKAN package ID: {package_id} with DOI: {doi}"
            )
            ckan_package_patch(
                package_id,
                {"publication_state": "reserved", "doi": doi},
                ckan,
            )

            response.status_code = datacite_response.get("status_code")
            return datacite_response

        # Else attempt to call DataCite API again
        retry_count += 1
        log.debug(
            "Failure publishing draft DOI, attempting again. " f"Retry: {retry_count}"
        )

        # Wait sleep_time seconds before trying to call DataCite again
        log.debug(f"Waiting {settings.DATACITE_SLEEP_TIME} seconds...")
        time.sleep(settings.DATACITE_SLEEP_TIME)

    # Get error message
    error_msg = get_error_message(datacite_response)

    # Send draft failed email
    await draft_failed_email(package_id, user_name, user_email, error_msg)

    # Return DataCite response
    response.status_code = datacite_response.get("status_code", 500)
    return datacite_response


@router.get("/request", name="Request approval to publish/update")
async def request_publish_or_update(
    package_id: Annotated[
        str, Query(alias="package-id", description="CKAN package id or name")
    ],
    request: Request,
    user=Depends(get_user),
):
    """Request approval from admin to publish or update dataset with DataCite.

    Send email to admin and user.
    If initial 'publication_state' is 'reserved' or 'published'
    then update to 'pub_pending'.
    """
    user_info = user.get("info")
    ckan = user.get("ckan")

    package = ckan_package_show(package_id, ckan)

    # Validate doi,
    # if doi not truthy or has invalid prefix then raises HTTPException
    validate_doi(package)

    # Extract publication_state
    publication_state = package.get("publication_state")
    if not publication_state:
        raise HTTPException(
            status_code=500, detail="Package does not have a 'publication_state'"
        )

    if not (user_name := user_info.get("display_name", None)):
        raise HTTPException(status_code=500, detail="Username not extracted")
    if not (user_email := user_info.get("email", None)):
        raise HTTPException(status_code=500, detail="User email not extracted")

    is_update = False
    match publication_state:
        # User requests publication,
        # if 'publication_state' fails to update then raises HTTPExcpetion
        case "reserved":
            publication_state = "pub_pending"

        # User requests metadata update
        case "published":
            publication_state = "pub_pending"
            is_update = True
            pass

        # Default case, raise HTTP excpetion
        case _:
            raise HTTPException(
                status_code=500,
                detail="Value for 'publication_state' cannot be processed",
            )

    # TODO test this works / sends
    await request_approval_email(
        package_id=package_id,
        user_name=user_name,
        user_email=user_email,
        approval_url=str(request.base_url).rstrip("/"),
        is_update=is_update,
    )

    log.debug(f"Updating package {package_id} to publication_state={publication_state}")
    response = ckan_package_patch(
        package_id, {"publication_state": publication_state}, ckan
    )
    log.debug(f"CKAN response: {response}")
    return JSONResponse(status_code=200, content={"success": True})


# TODO implement email sending
@router.get(
    "/publish",
    name="Publish/update dataset",
    status_code=200,
    responses={
        200: {
            "model": DoiSuccess,
            "description": "DOI successfully published/updated with DataCite",
        },
        422: {"model": DoiErrors},
        500: {"model": DoiErrors},
        502: {"model": DoiErrors},
    },
)
async def publish_or_update_datacite(
    package_id: Annotated[
        str, Query(alias="package-id", description="CKAN package id or name")
    ],
    response: Response,
    admin=Depends(get_admin),
):
    """Publish or update dataset with DataCite.

    Only authorized admin can use this endpoint.
    Sends email to admin and user.
    Updates 'publication_state' to 'published' in CKAN for datasets that were
    published the first time and had a value of ‘pub_pending’.
    """
    admin_info = admin.get("info")
    ckan = admin.get("ckan")

    # Get package,
    # if package_id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, ckan)

    # Extract publication_state
    publication_state = package.get("publication_state")
    if not publication_state:
        response.status_code = 500
        raise HTTPException(
            status_code=500, detail="Package does not have a 'publication_state'"
        )

    if not (user_name := admin_info.get("display_name", None)):
        raise HTTPException(status_code=500, detail="Username not extracted")
    if not (user_email := admin_info.get("email", None)):
        raise HTTPException(status_code=500, detail="User email not extracted")

    # Check if publication_state can be processed
    if publication_state not in ["pub_pending", "published"]:
        response.status_code = 500
        raise HTTPException(
            status_code=500,
            detail="Value for 'publication_state' cannot be processed",
        )

    # Publish/update dataset in Datacite,
    # if response status_code not in successful_status_codes
    # then try again "retries" times
    # Send notification email to admin and user
    successful_status_codes = range(200, 300)
    datacite_response = {}
    retry_count = 0

    while retry_count <= settings.DATACITE_RETRIES:
        # Send package to DataCite
        datacite_response = publish_datacite(package)

        if datacite_response.get("status_code") in successful_status_codes:
            log.debug(f"Updating package {package_id} to publication_state=published")
            response = ckan_package_patch(
                package_id, {"publication_state": "published"}, ckan
            )

            # Email user that publication complete
            await approval_granted_email(package_id, user_name, user_email)

            # Return successful datacite_response
            response.status_code = datacite_response.get("status_code")
            return datacite_response

        # Else attempt to call DataCite API again
        retry_count += 1

        # Wait sleep_time seconds before trying to call DataCite again
        time.sleep(settings.DATACITE_SLEEP_TIME)

    # Get error message
    error_msg = get_error_message(datacite_response)

    # TODO test this works / sends
    # TODO update endpoint to be more generic: datacite update failed
    await draft_failed_email(package_id, user_name, user_email, error_msg)

    # Return error datacite_response
    response.status_code = datacite_response.get("status_code", 500)
    return datacite_response
