"""DataCite API Router."""
import json
# Setup logging
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

# from app.api.doi import create_doi_draft
from app.auth import get_admin, get_user
from app.config import config_app
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
    datacite_failed_email,
    request_approval_email,
)
from app.logic.minter import create_db_doi
from app.logic.remote_ckan import ckan_package_patch, ckan_package_show

log = logging.getLogger(__name__)


# Setup datacite router
router = APIRouter(prefix="/datacite", tags=["datacite"])


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
    user=Depends(get_user),
):
    """Generate new DOI from DB and reserve draft DOI in DataCite.

       Updates 'publication_state' from '' to 'reserved'.

       This also updates the field 'doi' from a '' to the new doi from the db.

       If call to DataCite API fails then send error email to envidat@wsl.ch
    """
    user_info = user.get("info")
    ckan = user.get("ckan")

    package = ckan_package_show(package_id, ckan)

    if not (user_name := user_info.get("name", None)):
        log.error("Failure extracting username using Authorization header")
        raise HTTPException(status_code=500, detail="Username not extracted")
    if not (user_email := user_info.get("email", None)):
        log.error("Failure extracting email using Authorization header")
        raise HTTPException(status_code=500, detail="User email not extracted")

    # Validate publication_state is "" (value for newly created package is empty string)
    if publication_state := package.get("publication_state", None):
        log.error(f"Package '{package_id} already has value assigned for "
                  f"publication_state '{publication_state}'")
        raise HTTPException(status_code=400,
                            detail=f"Cannot reserve DOI because "
                                   f"package '{package_id}' already has value assigned "
                                   f"for publication_state: '{publication_state}'")

    # Check if doi has already been assigned
    if not (doi := package.get("doi", None)):

        # Mint new DOI in DOI database if it does not exist
        if (doi := await create_db_doi(user_name, package)) is None:
            log.error("Failed creating new DOI in database")
            return HTTPException(status_code=500, detail="New DOI creation failed")

        # Add DOI to dataset prior to DataCite call
        ckan_package_patch(package_id, {"doi": doi}, ckan)

    successful_status_codes = range(200, 300)
    datacite_response = {}
    retry_count = 0

    while retry_count <= config_app.DATACITE_RETRIES:
        datacite_response = reserve_draft_doi_datacite(doi)
        log.debug(f"DataCite response: {datacite_response}")

        if datacite_response.get("status_code") in successful_status_codes:
            log.debug(
                "DataCite draft reservation successful, "
                f"patching CKAN package ID: {package_id} with DOI: {doi}"
            )
            ckan_package_patch(
                package_id,
                {"publication_state": "reserved"},
                ckan,
            )

            return JSONResponse(
                datacite_response, status_code=datacite_response.get("status_code")
            )

        # Break loop if DataCite returns 422 status code,
        # this means that the DOI already has been taken
        elif datacite_response.get("status_code") == 422:
            log.debug(
                f"DataCite draft reservation failed for CKAN package ID:"
                f" {package_id} with DOI: {doi} "
                f"because the DOI had already been taken "
            )
            break

        # Else attempt to call DataCite API again
        retry_count += 1
        log.debug(
            "Failure publishing draft DOI, attempting again. " f"Retry: {retry_count}"
        )

        # Wait sleep_time seconds before trying to call DataCite again
        log.debug(f"Waiting {config_app.DATACITE_SLEEP_TIME} seconds...")
        time.sleep(config_app.DATACITE_SLEEP_TIME)

    # Get error message
    error_msg = get_error_message(datacite_response)

    # Send draft failed email
    await datacite_failed_email(package_id, user_name, user_email, error_msg)

    # Return DataCite response
    return JSONResponse(
        datacite_response, status_code=datacite_response.get("status_code", 500)
    )


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
        log.error("Package does not have 'publication_state' key")
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
            log.info("Publication state: reserved --> pub_pending")
            publication_state = "pub_pending"

        # User requests metadata update
        case "published":
            publication_state = "pub_pending"
            log.info("Publication state: published --> pub_pending (update requested)")
            is_update = True
            pass

        # User requests metadata update
        case "pub_pending":
            log.info("Publication already requested. Prompting admin again...")
            pass

        # Default case, raise HTTP excpetion
        case _:
            log.debug(
                "publication state field did not patch 'reserved' or 'published'. "
                "Skipping..."
            )
            raise HTTPException(
                status_code=500,
                detail="Value for 'publication_state' cannot be processed",
            )

    await request_approval_email(
        package_id=package_id,
        user_name=user_name,
        user_email=user_email,
        approval_url=str(request.base_url).rstrip("/"),
        is_update=is_update,
    )

    log.debug(f"Updating package {package_id} to publication_state={publication_state}")
    ckan_package_patch(package_id, {"publication_state": publication_state}, ckan)
    log.debug("Successfully updated CKAN package")
    return JSONResponse(status_code=200, content={"success": True})


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
    admin=Depends(get_admin),
):
    """Publish or update dataset with DataCite.

    Only authorized admin can use this endpoint.
    Sends email to admin and user.

    Updates 'publication_state' to 'published' in CKAN for datasets that were
    published the first time and had a value of 'pub_pending'.

    Also updates 'publication_state' to 'published' in CKAN for datasets that had the
    value of 'approved'.
    """
    admin_info = admin.get("info")
    ckan = admin.get("ckan")

    # Get package,
    # if package_id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, ckan)

    # Extract publication_state
    publication_state = package.get("publication_state")
    if not publication_state:
        log.error("Package does not have a 'publication_state'")
        raise HTTPException(
            status_code=500, detail="Package does not have a 'publication_state'"
        )

    # Get maintainer user name
    maintainer = package.get("maintainer", {})
    maintainer = json.loads(maintainer)
    maintainer_name = f"{maintainer.get('given_name', '')} {maintainer.get('name', '')}"
    if not (maintainer_email := maintainer.get("email", None)):
        raise HTTPException(status_code=500, detail="Package maintainer not extracted")
    if not (admin_email := admin_info.get("email", None)):
        raise HTTPException(status_code=500, detail="Admin email not extracted")

    # Check if publication_state can be processed
    if publication_state not in ["pub_pending", "published", "approved"]:
        log.error("Publication state is not one of the following:"
                  " 'pub_pending', 'published', 'approved'")
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

    while retry_count <= config_app.DATACITE_RETRIES:
        # Send package to DataCite
        try:
            datacite_response = publish_datacite(package)
            log.debug(f"DataCite response: {datacite_response}")
        except Exception as e:
            log.error(e)
            traceback = str(e)

        if datacite_response.get("status_code") in successful_status_codes:
            log.debug(
                "DataCite publish successful, patching "
                f"CKAN package ID: {package_id} to publication_state=published"
            )
            ckan_response = ckan_package_patch(
                package_id,
                {
                    "private": False,
                    "publication_state": "published",
                },
                ckan,
            )
            log.debug(f"CKAN package_patch response: {ckan_response}")

            # Email user that publication complete
            await approval_granted_email(
                package_id, maintainer_name, [maintainer_email, admin_email]
            )

            # Return successful datacite_response
            return JSONResponse(
                datacite_response, status_code=datacite_response.get("status_code")
            )

        # Else attempt to call DataCite API again
        retry_count += 1

        # Wait sleep_time seconds before trying to call DataCite again
        time.sleep(config_app.DATACITE_SLEEP_TIME)

    # Get error message
    if datacite_response:
        error_msg = get_error_message(datacite_response)
    else:
        error_msg = traceback

    await datacite_failed_email(
        package_id, maintainer_name, maintainer_email, error_msg
    )

    # Return error datacite_response
    return JSONResponse(
        datacite_response, status_code=datacite_response.get("status_code", 500)
    )
