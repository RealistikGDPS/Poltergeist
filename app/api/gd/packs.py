from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret
from poltergeist_core.services import packs

from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession

router = APIRouter()


@router.post("/getGJMapPacks21.php")
async def map_packs(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_map_packs(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(await packs.map_packs(ctx, request.page))

    return response.text(responses.serialise_map_packs(payload.packs, payload.page))


@router.post("/getGJGauntlets21.php")
async def gauntlets(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    response.parse(requests.parse_gauntlets(form), secret=Secret.COMMON, form=form)

    return response.text(responses.serialise_gauntlets(await packs.gauntlets(ctx)))
