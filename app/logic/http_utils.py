"""
Generic HTTP utilities for fetching and parsing remote resources.
"""

import asyncio
import json
import aiohttp
from fastapi import HTTPException


async def fetch_remote_json(
    url: str,
    timeout_seconds: int = 30,
) -> object:
    """
    Fetch and parse a remote JSON resource.

    Handles storage backends that may serve JSON with an unexpected Content-Type
    (e.g. application/octet-stream, which triggers a browser download)
    by ignoring the Content-Type header when parsing.

    Args:
        url: The URL to fetch JSON from.
        timeout_seconds: Total request timeout in seconds.

    Returns:
        The parsed JSON (type depends on the remote content).

    Raises:
        HTTPException: 502/504 for network/timeout issues, the remote
            status code for non-200 responses, or 422 for malformed or
            unexpected-shape JSON.
    """
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        resp.status, f"Could not download JSON from {url})"
                    )

                try:
                    data = await resp.json(content_type=None)
                except json.JSONDecodeError:
                    raise HTTPException(422, f"Remote JSON is invalid: {url}")

    except asyncio.TimeoutError:
        raise HTTPException(
            504, f"Timed out after {timeout_seconds}s while fetching {url}"
        )
    except aiohttp.ClientConnectorError:
        raise HTTPException(502, f"Could not connect to host for {url}")
    except aiohttp.ClientError as exc:
        raise HTTPException(502, f"Network error while fetching {url}: {exc}")

    return data
