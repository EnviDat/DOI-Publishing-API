"""Main init file for FastAPI."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.__version__ import __version__
from app.api.router import api_router, error_router
from app.config import settings
from app.db import init_db
from app.utils import load_dotenv_if_in_debug_mode

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=(
        "%(asctime)s.%(msecs)03d [%(levelname)s] "
        "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

load_dotenv_if_in_debug_mode()


def get_application() -> FastAPI:
    """Create app instance using config."""
    _app = FastAPI(
        title=settings.APP_NAME,
        description="API for publishing DOIs to DataCite.",
        version=__version__,
        license_info={
            "name": "MIT",
            "url": "https://gitlabext.wsl.ch/EnviDat/doi-publishing-api/-/raw/main/LICENSE",
        },
        debug=settings.DEBUG,
    )

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()

app.include_router(api_router)
app.include_router(error_router)


@app.on_event("startup")
async def startup_event():
    """Commands to run on server startup."""
    log.debug("Starting up FastAPI server.")
    init_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Commands to run on server shutdown."""
    log.debug("Shutting down FastAPI server.")
