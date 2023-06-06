"""DataCite API Router"""

from typing import Annotated
# from fastapi import Depends, Header
from fastapi import APIRouter, HTTPException, Security, Response, Query, Cookie
from fastapi.security.api_key import APIKeyHeader, APIKeyCookie

from app.auth import get_user
from app.logic.datacite import reserve_draft_doi_datacite, DoiSuccess, \
    DoiErrors
from app.logic.remote_ckan import get_ckan_package_show

# Setup logging
import logging

log = logging.getLogger(__name__)

# TODO verify signout
# TODO review exception formatting, consider returning generic response
# TODO add Swagger documentation of endpoints (title, description,
#  query parameters etc.)
# TODO implement authorization


# TODO review and remove dependencies if unused
# Setup datacite router
router = APIRouter(prefix="/datacite", tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )

# Setup authorization header
authorization_header = APIKeyHeader(name='Authorization',
                                    description='ckan cookie for logged in '
                                                'user passed in authorization '
                                                'header')

# Setup ckan cookie used for authorization
ckan_cookie = APIKeyCookie(name="ckan",
                           description="ckan cookie for logged in user")


# TODO review if authorizations should use cookie or header,
#  NOTE: cookie may not work when sending to an external site
# TODO remove endpoint after testing and move to logic/datacite.py,
#  call from doi/create_doi_draft
# TODO potentially remove responses, response arg
#  and response.status_code block
# TODO test dataset without doi
# TODO test with user id and package id (not just names)
@router.get(
    "/draft",
    name="Reserve draft DOI",
    status_code=201,
    responses={
        201: {"model": DoiSuccess,
              "description": "Draft DOI successfully reserved with DataCite"},
        422: {"model": DoiErrors},
        500: {"model": DoiErrors}
    }
)
def reserve_draft_doi(
        user: Annotated[str, Query(alias="user-id",
                                   description="CKAN user id or name")],
        package: Annotated[str, Query(alias="package-id",
                                      description="CKAN package id or name")],
        response: Response,
        # ckan: str = Security(ckan_cookie),
        authorization: str = Security(authorization_header),
):
    """
    Authenticate user, extract DOI from package, and reserve draft DOI in
    DataCite.
    """

    # Authorize user, if user invalid then raises HTTPException
    get_user(user, authorization)
    # user_info = get_user(user, ckan)

    # TODO clarify if doi will already be assigned to package
    #  or should be passed as arg
    # Get package
    # If package id invalid or user not authorized then raises HTTPException
    package = get_ckan_package_show(package, authorization)

    # Extract doi
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a doi")

    # TODO remove test_doi
    test_doi = "10.16904/envidat.test20"

    # TODO revert to calling DataCite API with doi, test
    # Reserve DOI in "Draft" state with DataCite,
    # datacite_response = reserve_draft_doi_datacite(doi)
    datacite_response = reserve_draft_doi_datacite(test_doi)

    # Set response status code
    response.status_code = datacite_response.get('status_code', 500)

    # Return formatted response
    return datacite_response


# TODO finish endpoint, currently WIP
# TODO potentially remove responses, response arg
#  and response.status_code block
# TODO test with user id and package id (not just names)
# TODO test dataset without doi
@router.get(
    "/request",
    name="Request approval to publish/update"
)
async def request_publish_approval(
        user: Annotated[str, Query(alias="user-id",
                                   description="CKAN user id or name")],
        package: Annotated[str, Query(alias="package-id",
                                      description="CKAN package id or name")],
        response: Response,
        authorization: str = Security(authorization_header)
):
    """
    Request approval from admin to publish or update dataset with DataCite.
    """

    # Authorize user, if user invalid then HTTPException raised
    get_user(user, authorization)

    # TODO review if doi validation needed
    # TODO check if doi prefix should be validated
    # Get package
    # If package id invalid or user not authorized then raises HTTPException
    package = get_ckan_package_show(package, authorization)
    # Extract doi
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a doi")

    # TODO start dev here

    return package
