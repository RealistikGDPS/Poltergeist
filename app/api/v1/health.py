from fastapi import APIRouter
from fastapi import Response

from app.api.v1 import response
from app.api.v1.context import RequiresContext
from app.services import health

router = APIRouter(prefix="/health")


@router.get("/")
async def check(ctx: RequiresContext) -> Response:
    response.unwrap(await health.check(ctx))

    return response.create(None)
