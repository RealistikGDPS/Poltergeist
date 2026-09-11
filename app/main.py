import asyncio
import sys

from poltergeist_core.utilities import logging
from poltergeist_core.utilities import loop

from app import api
from app import settings

logging.configure_from_yaml()
loop.install_optimal_loop()

logger = logging.get_logger(__name__)


async def _rebuild_leaderboards() -> None:
    # Local imports keep the ASGI component free of the one-shot tooling.
    from poltergeist_core.adapters import boomlings
    from poltergeist_core.adapters import mysql
    from poltergeist_core.adapters import redis
    from poltergeist_core.adapters import storage
    from poltergeist_core.services import leaderboards

    from app.api.context import HTTPTransactionContext

    pool = mysql.default()
    cache = redis.default()
    await pool.connect()
    await cache.initialise()

    ctx = HTTPTransactionContext(pool, cache, storage.default(), boomlings.default())
    total = await leaderboards.rebuild(ctx)
    logger.info("Leaderboard rebuild finished.", extra={"users": total})

    await cache.aclose()
    await pool.disconnect()


match settings.APP_COMPONENT:
    case "fastapi":
        asgi_app = api.create_app()
    case "rebuild_leaderboards":
        asyncio.run(_rebuild_leaderboards())
    case _:
        logger.error(
            "Unknown application component.",
            extra={"component": settings.APP_COMPONENT},
        )
        sys.exit(1)
