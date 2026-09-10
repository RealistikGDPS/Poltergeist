import asyncio
import sys

from app import api
from app import settings
from app.utilities import logging
from app.utilities import loop

logging.configure_from_yaml()
loop.install_optimal_loop()

logger = logging.get_logger(__name__)


async def _rebuild_leaderboards() -> None:
    # Local imports keep the ASGI component free of the one-shot tooling.
    from app.adapters import boomlings
    from app.adapters import mysql
    from app.adapters import redis
    from app.adapters import storage
    from app.api.context import HTTPTransactionContext
    from app.services import leaderboards

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
