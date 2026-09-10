from fastapi import APIRouter

from . import accounts
from . import comments
from . import levels
from . import lists
from . import misc
from . import packs
from . import rewards
from . import scores
from . import socials
from . import songs
from . import users

# NOTE: The client appends /database/... to the URL returned by getAccountURL,
# so the prefix is part of the protocol and not configurable.
_PREFIX = "/database"


def create_router() -> APIRouter:
    router = APIRouter(prefix=_PREFIX)

    router.include_router(accounts.router)
    router.include_router(users.router)
    router.include_router(socials.router)
    router.include_router(comments.router)
    router.include_router(levels.router)
    router.include_router(lists.router)
    router.include_router(packs.router)
    router.include_router(scores.router)
    router.include_router(songs.router)
    router.include_router(rewards.router)
    router.include_router(misc.router)

    return router
