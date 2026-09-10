import re
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import MutableMapping
from typing import Any

type Scope = MutableMapping[str, Any]
type Message = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]
type ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_REPEATED_SLASHES = re.compile(r"/{2,}")


def normalise(path: str) -> str:
    """Collapses runs of slashes: `/database///x.php` becomes `/database/x.php`.
    Clients patched to a same-length server URL pad it with slashes."""

    return _REPEATED_SLASHES.sub("/", path)


class CollapseSlashesMiddleware:
    """Rewrites the request path before routing. Pure ASGI so it costs one
    regex per request and nothing else."""

    __slots__ = ("_app",)  # One instance per application, but called per request.

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope["path"]
            collapsed = normalise(path)

            if collapsed != path:
                scope["path"] = collapsed
                scope["raw_path"] = collapsed.encode()

        await self._app(scope, receive, send)
