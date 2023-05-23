"""Mints a new DOI."""

import logging

from app.config import settings
from app.models.doi import DoiRealisation

log = logging.getLogger(__name__)


async def get_next_doi_suffix_id():
    """Get the next suffix ID in a prefix sequence."""
    suffix_ids = (
        await DoiRealisation.filter(
            prefix_id=settings.DOI_PREFIX,
            suffix_id__startswith=settings.DOI_SUFFIX_TAG,
        )
        .order_by("-suffix_id")
        .values_list("suffix_id", flat=True)
    )
    log.debug(f"Filtered suffix IDs: {suffix_ids}")

    numeric_ids = [int(suffix_id.split(".")[-1]) for suffix_id in suffix_ids]
    next_suffix_id = max(numeric_ids, default=0) + 1
    log.debug(f"Generating next DOI suffix in sequence: {next_suffix_id}")

    return next_suffix_id
