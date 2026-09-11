from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat.enums import Secret
from poltergeist_core.services import likes

from app.api.gd import response
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction

router = APIRouter()


@router.post("/likeGJItem211.php")
async def like(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_like(form), secret=Secret.COMMON, form=form)
    response.unwrap(await likes.like(ctx, session, request))

    return response.success()
