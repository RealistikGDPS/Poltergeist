from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret

from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.services import packs

router = APIRouter()


@router.post("/getGJMapPacks21.php")
async def map_packs(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(requests.parse_map_packs(form), secret=Secret.COMMON)
    payload = response.unwrap(await packs.map_packs(ctx, request.page))

    return response.text(responses.serialise_map_packs(payload.packs, payload.page))


@router.post("/getGJGauntlets21.php")
async def gauntlets(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    response.parse(requests.parse_gauntlets(form), secret=Secret.COMMON)

    return response.text(responses.serialise_gauntlets(await packs.gauntlets(ctx)))
