from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from poltergeist_core.services import health
from poltergeist_core.services import is_error

from app.api.context import HTTPContext
from app.api.interruption import ServiceInterruptionException

router = APIRouter()


@router.get("/health", include_in_schema=False)
async def check(ctx: Annotated[HTTPContext, Depends(HTTPContext)]) -> Response:
    """Answers the container healthcheck and the website's status probe; it
    is only reachable on the internal network."""

    result = await health.check(ctx)

    if is_error(result):
        raise ServiceInterruptionException(Response(status_code=result.status_code()))

    return Response(status_code=HTTPStatus.NO_CONTENT)
