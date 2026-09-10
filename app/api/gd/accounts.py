from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret

from app.api.context import client_ip
from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction
from app.services import accounts
from app.services import auth

router = APIRouter()


@router.post("/accounts/loginGJAccount.php")
async def login(form: RequiresForm, ctx: RequiresTransaction) -> Response:
    request = response.parse(requests.parse_login(form), secret=Secret.ACCOUNT)
    result = response.unwrap(await auth.login(ctx, request))

    return response.text(responses.serialise_login(result.account_id, result.user_id))


@router.post("/accounts/registerGJAccount.php")
async def register(
    form: RequiresForm, ctx: RequiresTransaction, http_request: Request
) -> Response:
    request = response.parse(requests.parse_register(form), secret=Secret.ACCOUNT)
    response.unwrap(await auth.register(ctx, request, ip=client_ip(http_request)))

    return response.success()


@router.post("/accounts/backupGJAccountNew.php")
async def backup(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_backup(form), secret=Secret.ACCOUNT)
    response.unwrap(await accounts.backup(ctx, session, request))

    return response.success()


@router.post("/accounts/syncGJAccountNew.php")
async def sync(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    response.parse(requests.parse_sync(form), secret=Secret.ACCOUNT)
    payload = response.unwrap(await accounts.sync(ctx, session))

    return response.text(
        responses.serialise_sync(
            payload.game_manager,
            payload.local_levels,
            payload.game_version,
            payload.binary_version,
            payload.rated_levels,
            payload.map_packs,
        )
    )


@router.post("/updateGJAccSettings20.php")
async def update_settings(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_update_settings(form), secret=Secret.COMMON)
    response.unwrap(await accounts.update_settings(ctx, session, request))

    return response.success()


@router.post("/getAccountURL.php")
async def account_url(form: RequiresForm) -> Response:
    response.parse(requests.parse_account_url(form), secret=Secret.COMMON)

    return response.text(accounts.account_url())
