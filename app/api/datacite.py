"""DataCite API Router"""


from typing import Annotated
# from fastapi import APIRouter, Depends, Header
from fastapi import APIRouter, HTTPException, Security, Response, Query
from fastapi.security.api_key import APIKeyHeader

from app.auth import get_user
from app.logic.datacite import get_package, reserve_draft_doi_datacite, \
    DoiSuccess, DoiErrors

import logging
log = logging.getLogger(__name__)


# TODO verify signout
# TODO review exception formatting
# TODO improve Swagger documentation of endpoints (title, description,
#  query parameters etc.)
# TODO implement authorization

# TODO remove dependencies if unused
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
@router.get("/draft",
            status_code=201,
            responses={
                201: {"model": DoiSuccess,
                      "description": "Draft DOI successfully reserved with "
                                     "DataCite"},
                403: {"model": DoiErrors},
                422: {"model": DoiErrors},
                500: {"model": DoiErrors}
            }
            )
def reserve_draft_doi(user: Annotated[str, Query(alias="user-id",
                                                 description="CKAN user id "
                                                             "or name")],
                      package: Annotated[str, Query(alias="package-id",
                                                    description="CKAN "
                                                                "package id "
                                                                "or name")],
                      response: Response,
                      authorization: str = Security(authorization_header)):
    """
    Authenticate user, extract DOI from package, and reserve draft DOI in
    DataCite.
    """

    # Check if user has email property, this indicates the user is authorized
    auth = get_user(user, authorization)
    if not auth.get('email'):
        raise HTTPException(status_code=403, detail="User not authorized")

    # Get package and extract doi
    package = get_package(package, authorization)
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Failed to parse doi from package")

    return package
