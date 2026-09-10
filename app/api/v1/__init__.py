from fastapi import APIRouter

from . import admin
from . import health

_PREFIX = "/api/v1"


def create_router() -> APIRouter:
    router = APIRouter(prefix=_PREFIX)

    router.include_router(health.router)
    router.include_router(admin.router)

    return router
