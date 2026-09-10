from typing import Any

from fastapi import Response
from fastapi import status
from pydantic import BaseModel

from app.api.interruption import ServiceInterruptionException
from app.services import ServiceError
from app.services import is_error
from app.utilities import logging

logger = logging.get_logger(__name__)


class BaseResponse[T](BaseModel):
    status: int
    data: T


def create(data: Any, *, status: int = status.HTTP_200_OK) -> Response:
    body = BaseResponse(status=status, data=data).model_dump_json()

    return Response(content=body, media_type="application/json", status_code=status)


def unwrap[T](result: ServiceError.OnSuccess[T]) -> T:
    if is_error(result):
        logger.debug(
            "API call interrupted by a service error.",
            extra={"error": result.resolve_name(), "status_code": result.status_code()},
        )

        raise ServiceInterruptionException(
            create(data=result.resolve_name(), status=result.status_code())
        )

    return result
