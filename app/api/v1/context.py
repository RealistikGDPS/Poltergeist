from typing import Annotated

from fastapi import Depends
from fastapi import Header
from poltergeist_core.services import admin

from app.api.context import HTTPContext
from app.api.context import HTTPTransactionContext
from app.api.context import transaction_context
from app.api.v1 import response


def _require_admin(x_api_key: Annotated[str | None, Header()] = None) -> None:
    response.unwrap(admin.verify_key(x_api_key))


RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
# NOTE: Function scope commits the transaction before the response is sent, so
# the client's next request always observes what it was just told succeeded.
RequiresTransaction = Annotated[
    HTTPTransactionContext, Depends(transaction_context, scope="function")
]
RequiresAdmin = Annotated[None, Depends(_require_admin)]
