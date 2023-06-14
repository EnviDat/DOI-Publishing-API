"""
Router used to import DOIs and associated metadata from external platforms
"""

from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.security import APIKeyHeader

# Setup logging
import logging

log = logging.getLogger(__name__)

# TODO test with production
# TODO finalize authorization method (header vs. cookie)

# Setup import router
router = APIRouter(prefix="/external-doi", tags=["external-doi"])

# Setup authorization header
authorization_header = APIKeyHeader(name='Authorization',
                                    description='ckan cookie for logged in '
                                                'user passed in authorization '
                                                'header')


class ExternalPlatform(str, Enum):
    zenodo = "zenodo"


@router.get(
    "/import",
    name="Import external DOI"
)
def import_external_doi(
        doi: Annotated[str, Query(description="DOI from external platform",
                                  example="10.5281/zenodo.6514932")],
        external_platform: Annotated[ExternalPlatform,
                                     Query(description="External platform "
                                                       "hosting DOI",
                                           example="zenodo")]
        = ExternalPlatform.zenodo
):
    """
    Import DOI and associated metadata from external plaforms
    into new EnviDat CKAN package.
    """

    # TODO START dev here

    return doi, external_platform


