"""DataCite API Router"""

from typing import Annotated
# from fastapi import Depends, Header
from fastapi import APIRouter, HTTPException, Security, Response, Query, Cookie
from fastapi.security.api_key import APIKeyHeader, APIKeyCookie

from app.auth import authorize_user, get_admin, authorize_admin
from app.config import settings
from app.logic.datacite import reserve_draft_doi_datacite, DoiSuccess, \
    DoiErrors
from app.logic.remote_ckan import ckan_package_show, ckan_package_patch

# Setup logging
import logging

log = logging.getLogger(__name__)

# TODO verify signout
# TODO review exception formatting, consider returning generic response
# TODO finalize authorization method (header vs. cookie)
# TODO review HTTPException formatting, possibly use more generic messages


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
        user_id: Annotated[str, Query(alias="user-id",
                                      description="CKAN user id or name")],
        package_id: Annotated[str, Query(alias="package-id",
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
    authorize_user(user_id, authorization)
    # user_info = get_user(user, ckan)

    # TODO clarify if doi will already be assigned to package
    #  or should be passed as arg
    # Get package
    # If package id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, authorization)

    # Extract doi
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a doi")

    # TODO remove test_doi
    test_doi = "10.16904/envidat.test24"

    # TODO revert to calling DataCite API with doi, test
    # Reserve DOI in "Draft" state with DataCite,
    # datacite_response = reserve_draft_doi_datacite(doi)
    datacite_response = reserve_draft_doi_datacite(test_doi)

    # Set response status code
    response.status_code = datacite_response.get('status_code', 500)

    # Return formatted response
    return datacite_response


# TODO potentially remove responses, response arg.
#  and response.status_code block
#  If response kept finalize format
# TODO test dataset without doi
# TODO implement email sending
@router.get(
    "/request",
    name="Request approval to publish/update"
)
async def request_publish_or_update(
        user_id: Annotated[str, Query(alias="user-id",
                                      description="CKAN user id or name")],
        package_id: Annotated[str, Query(alias="package-id",
                                         description="CKAN package id "
                                                     "or name")],
        # response: Response,
        authorization: str = Security(authorization_header)
):
    """
    Request approval from admin to publish or update dataset with DataCite.

    Send email to admin and user.
    If initial 'publication_state' is 'reserved' or 'published'
    then update to 'pub_pending'.
    """

    # Authorize user, if user invalid then HTTPException raised
    authorize_user(user_id, authorization)

    # Get package
    # If package id invalid or user not authorized then raises HTTPException
    package = ckan_package_show(package_id, authorization)

    # TODO extract doi and doi prefix validation to logic\datacite.py
    # Extract doi
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a 'doi'")

    # Validate doi prefix
    try:
        doi_prefix = settings.DOI_PREFIX
        prefix = doi.partition('/')
        if prefix != doi_prefix:
            raise HTTPException(status_code=403, detail="Invalid DOI prefix")
    except KeyError as e:
        raise HTTPException(status_code=500,
                            detail=f"Config setting does not exist: {e}")

    # Extract publication_state
    publication_state = package.get('publication_state')
    if not publication_state:
        raise HTTPException(status_code=500,
                            detail="Package does not have "
                                   "a 'publication_state'")

    # TODO remove
    publication_state = "published"

    # TODO refactor with if branching and simplify if 'publication_state'
    #  is 'pub_pending' for both "reserved" and "published" cases
    # Possible 'publication_state' values in EnviDat CKAN:
    # ['', 'reserved', 'pub_requested', 'pub_pending', 'approved', 'published']
    # Send email to admin  publication_state
    match publication_state:

        # User requests publication
        case "reserved":

            # TODO send “Publication request” email to admin and user

            data = {'publication_state': 'pub_pending'}
            package = ckan_package_patch(package_id, data, authorization)

        # User requests metadata update
        case "published":

            # TODO send "Update request" email to admin and user

            # TODO clairify appropriate 'publication_state'
            data = {'publication_state': 'pub_pending'}
            package = ckan_package_patch(package_id, data, authorization)

        # Default case, raise HTTP excpetion
        case _:
            raise HTTPException(status_code=500,
                                detail="Value for 'publication_state' cannot "
                                       "be processed")

    return {'publication_state': package.get('publication_state')}

