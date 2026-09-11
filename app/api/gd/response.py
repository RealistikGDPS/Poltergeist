from collections.abc import Mapping
from typing import Protocol

from fastapi import Response
from fastapi.responses import PlainTextResponse
from gdformat import ParseResult
from gdformat import codes
from gdformat import is_error as is_parse_error
from gdformat.enums import Secret
from gdformat.requests import Client
from poltergeist_core.services import ServiceError
from poltergeist_core.services import clients
from poltergeist_core.services import is_error
from poltergeist_core.utilities import logging

from app.api.interruption import ServiceInterruptionException

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
    """The only bridge from a service error to a protocol response. The client
    only ever sees a bare code, so the reason is logged here for operators."""

    if is_error(result):
        logger.info(
            "Request refused.",
            extra={"error": result.resolve_name(), "code": result.code()},
        )

        raise ServiceInterruptionException(code(result.code()))

    return result


def parse[T: _HasClient](
    result: ParseResult[T], *, secret: Secret, form: Mapping[str, str]
) -> T:
    """Rejects malformed forms and clients that are outdated or carry the
    wrong secret for the endpoint. A parse failure names the endpoint and the
    keys the client sent, since it usually means a protocol mismatch."""

    if is_parse_error(result):
        logger.warning(
            "Request form failed to parse.",
            extra={"error": result.value, "keys": sorted(form)},
        )

        raise ServiceInterruptionException(failure())

    unwrap(clients.validate(result.client, secret))

    return result
