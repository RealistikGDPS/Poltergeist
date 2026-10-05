import uuid

from poltergeist_core.utilities import logging

from .paths import ASGIApp
from .paths import Receive
from .paths import Scope
from .paths import Send


class RequestTraceMiddleware:
    __slots__ = ("_app",)

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        logging.add_context(uuid=str(uuid.uuid4()), path=scope["path"])

        try:
            await self._app(scope, receive, send)
        finally:
            logging.clear_context()
