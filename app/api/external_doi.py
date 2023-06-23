"""Router used to convert DOIs and associated metadata from external platforms
into EnviDat CKAN package format.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Query, Response, Security
from fastapi.security import APIKeyHeader

from app.auth import get_user
from app.logic.external_doi.constants import (
    ConvertError,
    ConvertSuccess,
    ExternalPlatform,
)
from app.logic.external_doi.utils import convert_doi, get_doi_external_platform
from app.logic.external_doi.zenodo import convert_zenodo_doi

log = logging.getLogger(__name__)

# TODO test with production

# Setup external-doi router
router = APIRouter(prefix="/external-doi", tags=["external-doi"])

# Setup authorization header
authorization_header = APIKeyHeader(
    name="Authorization",
    description="ckan cookie for logged in user passed in authorization header",
)


@router.get(
    "/convert",
    name="Convert external DOI",
    status_code=200,
    responses={
        200: {
            "model": ConvertSuccess,
            "description": "External DOI successfully converted to "
            "EnviDat package format",
        },
        400: {"model": ConvertError},
        404: {"model": ConvertError},
        500: {"model": ConvertError},
    },
)
def convert_external_doi(
    doi: Annotated[
        str,
        Query(
            description="DOI from external platform",
            examples={
                "doi only": {"value": "10.5281/zenodo.5230562"},
                "doi with url": {"value": "https://doi.org/10.5281/zenodo.5230562"},
            },
        ),
    ],
    owner_org: Annotated[
        str,
        Query(
            description="'owner_org' assigned to user in EnviDat CKAN",
            example="bd536a0f-d6ac-400e-923c-9dd351cb05fa",
        ),
    ],
    response: Response,
    authorization: str = Security(authorization_header),
    add_placeholders: Annotated[
        bool,
        Query(
            alias="add-placeholders",
            description="If true placeholder values are added for "
            "required EnviDat package fields",
        ),
    ] = False,
):
    """Convert DOI and associated metadata from external plaforms
    into EnviDat CKAN package formatted json.
    """
    # Authorize user, if user invalid then raises HTTPException
    user = get_user(authorization)

    # Get external platform name and call corresponding API,
    # then convert the DOI's metadata to EnviDat CKAN package format
    external_platform = get_doi_external_platform(doi)

    match external_platform:
        case ExternalPlatform.ZENODO:
            result = convert_zenodo_doi(doi, owner_org, user, add_placeholders)

        case _:
            result = convert_doi(doi, owner_org, user, add_placeholders)

    response.status_code = result.get("status_code", 500)
    return result
