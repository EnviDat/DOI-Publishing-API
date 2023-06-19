"""DataCite API Router"""

import time
from typing import Annotated
from fastapi import APIRouter, HTTPException, Security, Response, Query, \
    Depends
from fastapi.security.api_key import APIKeyHeader

# from app.api.doi import create_doi_draft
from app.auth import get_user, get_admin
from app.logic.datacite import reserve_draft_doi_datacite, DoiSuccess, \
    DoiErrors, validate_doi, publish_datacite
from app.logic.remote_ckan import ckan_package_show, ckan_package_patch
from app.config import settings

# Setup logging
import logging

log = logging.getLogger(__name__)

# TODO test with production
# TODO verify signout
# TODO review HTTPException formatting, possibly use more generic messages

# TODO review implementation of auth and dependencies


# TODO review and remove dependencies if unused
# Setup datacite router
router = APIRouter(prefix="/datacite",
                   tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )

# Setup authorization header
authorization_header = APIKeyHeader(name='Authorization',
                                    description='ckan cookie for logged in '
                                                'user passed in authorization '
                                                'header')


# TODO possibly remove similar endpoint in doi/create_doi_draft
@router.get(
    "/draft",
    name="Reserve draft DOI",
    status_code=201,
    responses={
        201: {"model": DoiSuccess,
              "description": "Draft DOI successfully reserved with DataCite"},
        422: {"model": DoiErrors},
        500: {"model": DoiErrors},
        502: {"model": DoiErrors}
    }
)
async def reserve_draft_doi(
        package_id: Annotated[str, Query(alias="package-id",
                                         description="CKAN package id or "
                                                     "name")],
        response: Response,
        authorization: str = Security(authorization_header)
):
    """
    Authenticate user, extract DOI from package, and reserve draft DOI in
    DataCite.
    """

    # TODO review authorization implementation
    # Authorize user, if user invalid then raises HTTPException
    user = get_user(authorization)

    # Extract variables needed from config
    retries = settings.DATACITE_RETRIES
    sleep_time = settings.DATACITE_SLEEP_TIME

    # Get package
    # If package id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, authorization)

    # TODO clarify if doi will already be assigned to package
    #  or will be assigned after reserving doi with DataCite
    # TODO possibly validate doi by calling validate_doi()
    # Get new DOI
    # doi = await create_doi_draft(package_id)
    # print(doi)

    # Extract doi
    # doi = package.get('doi')
    # if not doi:
    #     response.status_code = 500
    #     raise HTTPException(status_code=500,
    #                         detail="Package does not have a doi")

    # TODO remove test_doi
    test_doi = "10.16904/envidat.test40"

    # Reserve DOI in draft state with DataCite,
    # if response status_code not in successful_status_codes
    # then try again "retries" times
    # datacite_response = reserve_draft_doi_datacite(doi)
    successful_status_codes = range(200, 300)
    datacite_response = {}
    retry_count = 0

    while retry_count <= retries:

        # TODO revert to calling DataCite API with doi
        datacite_response = reserve_draft_doi_datacite(test_doi)

        if datacite_response.get("status_code") in successful_status_codes:
            # TODO update package doi value with doi variable
            # Update publication_state and doi in CKAN package
            data = {
                "publication_state": "reserved",
                "doi": test_doi
            }
            ckan_package_patch(package_id, data, authorization)

            # TODO email admin that DOI was successfully reserved with DataCite

            response.status_code = datacite_response.get('status_code')
            return datacite_response

        # Else attempt to call DataCite API again
        retry_count += 1

        # Wait sleep_time seconds before trying to call DataCite again
        time.sleep(sleep_time)

    # TODO email admin to notify of failure to reserve DOI with datacite

    response.status_code = datacite_response.get('status_code', 500)
    return datacite_response


# TODO implement email sending
# TODO finalize response returned
@router.get(
    "/request",
    name="Request approval to publish/update"
)
async def request_publish_or_update(
        package_id: Annotated[str, Query(alias="package-id",
                                         description="CKAN package id "
                                                     "or name")],
        authorization: str = Security(authorization_header)
):
    """
    Request approval from admin to publish or update dataset with DataCite.

    Send email to admin and user.
    If initial 'publication_state' is 'reserved' or 'published'
    then update to 'pub_pending'.
    """

    # TODO review authorization implementation
    # Authorize user, if user invalid then HTTPException raised
    user = get_user(authorization)

    # Get package,
    # if package_id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, authorization)

    # Validate doi,
    # if doi not truthy or has invalid prefix then raises HTTPException
    validate_doi(package)

    # Extract publication_state
    publication_state = package.get('publication_state')
    if not publication_state:
        raise HTTPException(status_code=500,
                            detail="Package does not have "
                                   "a 'publication_state'")

    # Send email to admin requesting publication/update
    match publication_state:

        # User requests publication,
        # if 'publication_state' fails to update then raises HTTPExcpetion
        case "reserved":

            # TODO send “Publication request” email to admin and user

            data = {'publication_state': 'pub_pending'}
            ckan_package_patch(package_id, data, authorization)

        # User requests metadata update
        case "published":
            # TODO send "Update request" email to admin and user
            pass

        # Default case, raise HTTP excpetion
        case _:
            raise HTTPException(status_code=500,
                                detail="Value for 'publication_state' cannot "
                                       "be processed")

    # TODO finalize return value
    return "Successfully requested approval to publish or update dataset"


# TODO implement email sending
@router.get(
    "/publish",
    name="Publish/update dataset",
    status_code=200,
    responses={
        200: {"model": DoiSuccess,
              "description": "DOI successfully published/updated "
                             "with DataCite"},
        422: {"model": DoiErrors},
        500: {"model": DoiErrors},
        502: {"model": DoiErrors}
    }
)
async def publish_or_update_datacite(
        package_id: Annotated[str, Query(alias="package-id",
                                         description="CKAN package id "
                                                     "or name")],
        response: Response,
        authorization: str = Security(authorization_header)
        # admin=Depends(get_admin)
):
    """
    Publish or update dataset with DataCite.

    Only authorized admin can use this endpoint.
    Sends email to admin and user.
    Updates 'publication_state' to 'published' in CKAN for datasets that were
    published the first time and had a value of ‘pub_pending’.
    """

    # TODO review authorization implementation
    # Authorize admin user, if authorization invalid then HTTPException raised
    admin = get_admin(get_user(authorization))

    # Extract variables needed from config
    retries = settings.DATACITE_RETRIES
    sleep_time = settings.DATACITE_SLEEP_TIME

    # Get package,
    # if package_id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, authorization)

    # Extract publication_state
    publication_state = package.get('publication_state')
    if not publication_state:
        response.status_code = 500
        raise HTTPException(status_code=500,
                            detail="Package does not have "
                                   "a 'publication_state'")

    # Check if publication_state can be processed
    if publication_state not in ['pub_pending', 'published']:
        response.status_code = 500
        raise HTTPException(status_code=500,
                            detail="Value for 'publication_state' cannot "
                                   "be processed")

    # Publish/update dataset in Datacite,
    # if response status_code not in successful_status_codes
    # then try again "retries" times
    # Send notification email to admin and user
    successful_status_codes = range(200, 300)
    datacite_response = {}
    retry_count = 0

    while retry_count <= retries:

        # Send package to DataCite
        datacite_response = publish_datacite(package)

        if datacite_response.get('status_code') in successful_status_codes:

            if publication_state == 'pub_pending':
                # Update publication_state in CKAN package
                data = {'publication_state': 'published'}
                ckan_package_patch(package_id, data, authorization)

                # TODO send "Publication Finished"
                #  email to admin and maintainer

            else:
                # TODO send "DOI Metadata Updated" to only admin
                pass

            # Return successful datacite_response
            response.status_code = datacite_response.get('status_code')
            return datacite_response

        # Else attempt to call DataCite API again
        retry_count += 1

        # Wait sleep_time seconds before trying to call DataCite again
        time.sleep(sleep_time)

    # TODO email admin to notify of failure to publish/update DOI with datacite

    # Return error datacite_response
    response.status_code = datacite_response.get('status_code', 500)
    return datacite_response
