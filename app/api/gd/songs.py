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
from app.services import songs

router = APIRouter()


@router.post("/getGJSongInfo.php")
async def song_info(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_song_info(form), secret=Secret.COMMON)
    song = response.unwrap(await songs.song_info(ctx, request.song_id))

    return response.text(responses.serialise_song_info(song))


@router.post("/getGJTopArtists.php")
async def top_artists(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(requests.parse_top_artists(form), secret=Secret.COMMON)
    payload = response.unwrap(await songs.top_artists(ctx, request.page))

    return response.text(responses.serialise_top_artists(payload.artists, payload.page))


@router.post("/getCustomContentURL.php")
async def custom_content_url() -> Response:
    return response.text(songs.custom_content_url())
