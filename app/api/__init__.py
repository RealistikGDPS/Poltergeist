import uuid
from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response

from app.adapters import boomlings
from app.adapters import mysql
from app.adapters import redis
from app.adapters import storage
from app.utilities import logging

from . import gd
from . import v1
from .interruption import ServiceInterruptionException

logger = logging.get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await app.state.mysql.connect()
    logger.info("Connected to the MySQL database.")
    await app.state.redis.initialise()
    logger.info("Connected to the Redis database.")

    yield

    await app.state.boomlings.close()
    await app.state.redis.aclose()
    await app.state.mysql.disconnect()
    logger.info("Disconnected from the databases.")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=_lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    initialise_mysql(app)
    initialise_redis(app)
    initialise_storage(app)
    initialise_boomlings(app)
    initialise_interruptions(app)
    initialise_request_tracing(app)
    create_routes(app)

    logger.debug("Finalised the app instance.")

    return app


def initialise_mysql(app: FastAPI) -> None:
    app.state.mysql = mysql.default()
    logger.debug("Attached MySQL to the app instance.")


def initialise_redis(app: FastAPI) -> None:
    app.state.redis = redis.default()
    logger.debug("Attached Redis to the app instance.")


def initialise_storage(app: FastAPI) -> None:
    app.state.storage = storage.default()
    logger.debug("Attached object storage to the app instance.")


def initialise_boomlings(app: FastAPI) -> None:
    app.state.boomlings = boomlings.default()
    logger.debug("Attached the Boomlings client to the app instance.")


def initialise_interruptions(app: FastAPI) -> None:
    @app.exception_handler(ServiceInterruptionException)
    async def handle_interruption(
        _: Request, exception: ServiceInterruptionException
    ) -> Response:
        return exception.response

    logger.debug("Initialised the service interruption handler.")


def initialise_request_tracing(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_request(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.uuid = str(uuid.uuid4())
        logging.add_context(uuid=request.state.uuid)

        try:
            return await call_next(request)
        finally:
            logging.clear_context()

    logger.debug("Initialised request tracing.")


def create_routes(app: FastAPI) -> None:
    app.include_router(gd.create_router())
    app.include_router(v1.create_router())
    logger.debug("Attached routers to the app instance.")
