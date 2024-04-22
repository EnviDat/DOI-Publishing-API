"""Main init file for FastAPI."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.__version__ import __version__
from app.api.router import api_router, error_router
from app.config import config_app, log_level
from app.db import init_db, close_db

logging.basicConfig(
    level=log_level,
    format=(
        "%(asctime)s.%(msecs)03d [%(levelname)s] "
        "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    init_db(app)
    yield
    # Clean up the db connections
    await close_db()

def get_application() -> FastAPI:
    """Create app instance using config."""
    _app = FastAPI(
        title=config_app.__NAME__,
        description="API for publishing DOIs to DataCite and importing DOIs "
        "from external platforms.",
        version=config_app.APP_VERSION,
        license_info={
            "name": "MIT",
            "url": "https://gitlabext.wsl.ch/EnviDat/doi-publishing-api/-/raw/main/LICENSE",
        },
        debug=config_app.DEBUG,
        root_path=config_app.ROOT_PATH,
        lifespan=lifespan,
        #openapi_prefix=config_app.PROXY_PREFIX,
    )

    log.debug(f"Allowed CORS origins: {config_app.BACKEND_CORS_ORIGINS}")
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=config_app.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()

app.include_router(api_router)
app.include_router(error_router)


