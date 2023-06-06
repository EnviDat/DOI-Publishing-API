"""DataCite API Router"""


from typing import Annotated
# from fastapi import Depends, Header
from fastapi import APIRouter, HTTPException, Security, Response, Query
from fastapi.security.api_key import APIKeyHeader

from app.auth import get_user
from app.logic.datacite import reserve_draft_doi_datacite, DoiSuccess, \
    DoiErrors
from app.logic.remote_ckan import get_ckan_package_show


# Setup logging
import logging
log = logging.getLogger(__name__)


# TODO verify signout
# TODO review exception formatting
# TODO add Swagger documentation of endpoints (title, description,
#  query parameters etc.)
# TODO implement authorization


# TODO review and remove dependencies if unused
# Setup datacite router
router = APIRouter(prefix="/datacite", tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )

# Setup authorization
authorization_header = APIKeyHeader(name='Authorization')


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
        authorization: str = Security(authorization_header)
):
    """
    Authenticate user, extract DOI from package, and reserve draft DOI in
    DataCite.
    """

    # Authorize user, if user invalid then HTTPException raised
    get_user(user, authorization)

    # TODO clarify if doi will already be assigned to package
    #  or should be passed as arg
    # Get package and extract doi
    package = get_ckan_package_show(package, authorization)
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a doi")

    # TODO remove test_doi
    test_doi = "10.16904/envidat.test19"

    # TODO revert to calling DataCite API with doi, test
    # Reserve DOI in "Draft" state with DataCite,
    # datacite_response = reserve_draft_doi_datacite(doi)
    datacite_response = reserve_draft_doi_datacite(test_doi)

    # Set response status code
    response.status_code = datacite_response.get('status_code', 500)

    # Return formatted response
    return datacite_response
