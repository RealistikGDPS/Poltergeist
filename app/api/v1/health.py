from fastapi import APIRouter
from fastapi import Response
from poltergeist_core.services import health

from app.api.v1 import response
from app.api.v1.context import RequiresContext

router = APIRouter(prefix="/health")


@router.get("/")
async def check(ctx: RequiresContext) -> Response:
    response.unwrap(await health.check(ctx))

    return response.create(None)
