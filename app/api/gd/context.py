from typing import Annotated

from fastapi import Depends
from fastapi import Request
from gdformat import is_error as is_parse_error
from gdformat import requests
from gdformat.enums import Secret

from app.api.context import HTTPContext
from app.api.context import HTTPTransactionContext
from app.api.context import transaction_context
from app.api.gd import response
from app.services import auth
from app.services.auth import Session

type Form = dict[str, str]

_SECRETS = frozenset(secret.value for secret in Secret)


async def _read_form(request: Request) -> Form:
    form = await request.form()

    return {key: value for key, value in form.items() if isinstance(value, str)}


async def _authenticate(
    request: Request, form: Annotated[Form, Depends(_read_form)]
) -> Session:
    """Every request to the game endpoints carries `accountID` and `gjp2`;
    parsing them as a mod access request reads exactly those and the client."""

    parsed = requests.parse_mod_access(form)

    if is_parse_error(parsed):
        return response.unwrap(auth.AuthError.UNAUTHENTICATED)

    if parsed.client.secret not in _SECRETS:
        response.unwrap(auth.AuthError.UNAUTHENTICATED)

    return response.unwrap(
        await auth.authenticate(HTTPContext(request), parsed.auth, parsed.client)
    )


RequiresForm = Annotated[Form, Depends(_read_form)]
RequiresContext = Annotated[HTTPContext, Depends(HTTPContext)]
# NOTE: Function scope commits the transaction before the response is sent, so
# the client's next request always observes what it was just told succeeded.
RequiresTransaction = Annotated[
    HTTPTransactionContext, Depends(transaction_context, scope="function")
]
RequiresSession = Annotated[Session, Depends(_authenticate)]
