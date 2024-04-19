"""Utils module for DOI Publishing API, for debugging."""

import logging

log = logging.getLogger(__name__)

def fix_url_double_slash(url):
    """Removed double slashes from a URL.

    Sometimes double slashes can be added by redirects, proxies, etc.
    """
    parts = url.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
        rest = rest.replace("//", "/")
        return f"{scheme}://{rest}"
    return url
