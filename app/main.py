"""Main init file for FastAPI."""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from contextlib import asynccontextmanager
#from tortoise.contrib.fastapi import RegisterTortoise

from app.api.router import api_router, error_router
from app.config import config_app, log_level
from app.db import init_db

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

## The below work with Tortoise_orm 0.20.1 and the fix for this is currently in develop
## https://github.com/tortoise/tortoise-orm/commit/7ded5c7cdbdcdc56d5def36c8cf865abc27c9823
#TORTOISE_ORM = {
#    "connections": {"default": config_app.DB_URI},
#    "apps": {
#        config_app.__NAME__: {
#            "models": [
#                "app.models.doi",
#            ],
#            "default_connection": "default",
#        },
#    },
#    "routers": [],
#    "use_tz": False,
#    "timezone": "UTC",
#}

#@asynccontextmanager
#async def lifespan(app: FastAPI):
    # app startup
#    async with RegisterTortoise(
#        app,
#        config=TORTOISE_ORM,
#        add_exception_handlers=True,
#    ):
        # db connected
#        yield
        # app teardown
    # db connections closed

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
        #lifespan=lifespan,
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

@app.on_event("startup")
async def startup_event():
    """Commands to run on server startup."""
    log.debug("Starting up FastAPI server.")
    init_db(app)

