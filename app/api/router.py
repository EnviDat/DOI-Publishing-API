"""Root router to import all other routers."""

import logging
from typing import Callable

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from app.api import datacite, external_doi, approval, doi, prefix

log = logging.getLogger(__name__)


class RouteErrorHandler(APIRoute):
    """Custom APIRoute that handles application errors and exceptions."""

    def get_route_handler(self) -> Callable:
        """Original route handler for extension."""
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            """Route handler with improved logging."""
            try:
                return await original_route_handler(request)
            except Exception as e:
                if isinstance(e, HTTPException):
                    raise Exception from e
                log.exception(f"Uncaught error: {e}")

                raise HTTPException from e(status_code=500, detail=str(e))

        return custom_route_handler


api_router = APIRouter()
api_router.include_router(datacite.router)
api_router.include_router(external_doi.router)
api_router.include_router(doi.router)
api_router.include_router(prefix.router)
api_router.include_router(approval.router)

error_router = APIRouter(route_class=RouteErrorHandler)


@api_router.get("/", include_in_schema=False)
async def home():
    """Redirect home to docs."""
    return RedirectResponse("/docs")
