import ipaddress

from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import ChestType
from gdformat.enums import Secret
from gdformat.enums import TimelyType
from poltergeist_core.services import levels
from poltergeist_core.services import moderation
from poltergeist_core.services import timely

from app.api.context import client_ip
from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction

router = APIRouter()


@router.post("/uploadGJLevel21.php")
async def upload(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_upload_level(form), secret=Secret.COMMON, form=form
    )
    level_id = response.unwrap(await levels.upload(ctx, session, request))

    return response.code(level_id)


@router.post("/downloadGJLevel22.php")
async def download(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_download_level(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(await levels.download(ctx, session, request))

    return response.text(
        responses.serialise_level_download(
            payload.level, payload.songs, creator=payload.creator
        )
    )


@router.post("/getGJLevels21.php")
async def search(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_level_search(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(await levels.search(ctx, session, request))

    return response.text(
        responses.serialise_level_search(
            payload.levels, payload.creators, payload.songs, payload.page
        )
    )


@router.post("/deleteGJLevelUser20.php")
async def delete(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_level(form), secret=Secret.LEVEL, form=form
    )
    response.unwrap(await levels.delete(ctx, session, request.level_id))

    return response.success()


@router.post("/updateGJDesc20.php")
async def update_description(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_update_description(form), secret=Secret.COMMON, form=form
    )

    response.unwrap(
        await levels.update_description(
            ctx, session, request.level_id, request.description
        )
    )

    return response.success()


@router.post("/reportGJLevel.php")
async def report(
    form: RequiresForm, ctx: RequiresTransaction, http_request: Request
) -> Response:
    request = response.parse(
        requests.parse_report_level(form), secret=Secret.COMMON, form=form
    )
    ip = ipaddress.ip_address(client_ip(http_request)).packed
    response.unwrap(await levels.report(ctx, request.level_id, user_id=None, ip=ip))

    return response.success()


@router.post("/rateGJStars211.php")
async def rate_stars(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_rate_stars(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await levels.rate_stars(ctx, session, request))

    return response.success()


@router.post("/suggestGJStars20.php")
async def suggest_stars(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_suggest_stars(form), secret=Secret.MOD, form=form
    )
    response.unwrap(await moderation.suggest_stars(ctx, session, request))

    return response.success()


@router.post("/rateGJDemon21.php")
async def rate_demon(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_rate_demon(form), secret=Secret.MOD, form=form
    )
    level_id = response.unwrap(await moderation.rate_demon(ctx, session, request))

    return response.code(level_id)


@router.post("/getGJDailyLevel.php")
async def daily_level(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_timely(form), secret=Secret.COMMON, form=form
    )
    current = response.unwrap(await timely.current(ctx, request.timely_type))

    if request.timely_type is not TimelyType.EVENT:
        return response.text(
            responses.serialise_timely(current.timely.wire_id, current.seconds_left)
        )

    return response.text(
        responses.serialise_event(
            current.timely.wire_id,
            request.chk or 0,
            current.timely.id,
            current.timely.chest_type or ChestType.EVENT,
            current.rewards,
        )
    )
