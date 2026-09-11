from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret
from poltergeist_core.services import lists

from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction

router = APIRouter()


@router.post("/getGJLevelLists.php")
async def search(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_list_search(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(await lists.search(ctx, session, request))

    return response.text(
        responses.serialise_list_search(payload.lists, payload.creators, payload.page)
    )


@router.post("/uploadGJLevelList.php")
async def upload(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_upload_list(form), secret=Secret.COMMON, form=form
    )
    list_id = response.unwrap(await lists.upload(ctx, session, request))

    return response.code(list_id)


@router.post("/deleteGJLevelList.php")
async def delete(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_list(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await lists.delete(ctx, session, request.list_id))

    return response.success()
