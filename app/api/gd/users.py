from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret

from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction
from app.services import users

router = APIRouter()


@router.post("/getGJUserInfo20.php")
async def profile(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(requests.parse_profile(form), secret=Secret.COMMON)
    user = response.unwrap(await users.profile(ctx, session, request.target_account_id))

    return response.text(responses.serialise_profile(user))


@router.post("/getGJUsers20.php")
async def search(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(requests.parse_user_search(form), secret=Secret.COMMON)
    payload = response.unwrap(await users.search(ctx, request.query, request.page))

    return response.text(responses.serialise_user_search(payload.users, payload.page))


@router.post("/updateGJUserScore22.php")
async def update_stats(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_update_stats(form), secret=Secret.COMMON)
    user_id = response.unwrap(await users.update_stats(ctx, session, request))

    return response.code(user_id)


@router.post("/getGJScores20.php")
async def leaderboard(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(requests.parse_leaderboard(form), secret=Secret.COMMON)
    rows = response.unwrap(await users.leaderboard(ctx, session, request))

    return response.text(
        responses.serialise_leaderboard(rows, viewer_account_id=session.user.id)
    )


@router.post("/requestUserAccess.php")
async def mod_access(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    response.parse(requests.parse_mod_access(form), secret=Secret.COMMON)

    return response.code(await users.mod_access(ctx, session))
