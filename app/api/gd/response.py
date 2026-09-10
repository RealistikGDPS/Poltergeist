from typing import Protocol

from fastapi import Response
from fastapi.responses import PlainTextResponse
from gdformat import ParseResult
from gdformat import codes
from gdformat import is_error as is_parse_error
from gdformat.enums import Secret
from gdformat.requests import Client

from app.api.interruption import ServiceInterruptionException
from app.services import ServiceError
from app.services import clients
from app.services import is_error
from app.utilities import logging

logger = logging.get_logger(__name__)


class _HasClient(Protocol):
    @property
    def client(self) -> Client: ...


def text(content: str) -> Response:
    return PlainTextResponse(content)


def code(value: int) -> Response:
    return text(codes.serialise_code(value))


def success() -> Response:
    return text(codes.SUCCESS)


def failure() -> Response:
    return text(codes.FAILURE)


def unwrap[T](result: ServiceError.OnSuccess[T]) -> T:
    """The only bridge from a service error to a protocol response."""

    if is_error(result):
        logger.debug(
            "Request interrupted by a service error.",
            extra={"error": result.resolve_name(), "code": result.code()},
        )

        raise ServiceInterruptionException(code(result.code()))

    return result


def parse[T: _HasClient](result: ParseResult[T], *, secret: Secret) -> T:
    """Rejects malformed forms and clients that are outdated or carry the
    wrong secret for the endpoint."""

    if is_parse_error(result):
        logger.debug("Request form failed to parse.", extra={"error": result.value})

        raise ServiceInterruptionException(failure())

    unwrap(clients.validate(result.client, secret))

    return result
