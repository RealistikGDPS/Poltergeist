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
from app.services import socials

router = APIRouter()


@router.post("/uploadFriendRequest20.php")
async def send_friend_request(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_send_friend_request(form), secret=Secret.COMMON, form=form
    )

    response.unwrap(
        await socials.send_friend_request(
            ctx, session, request.target_account_id, request.message
        )
    )

    return response.success()


@router.post("/acceptGJFriendRequest20.php")
async def accept_friend_request(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_accept_friend_request(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(
        await socials.accept_friend_request(ctx, session, request.target_account_id)
    )

    return response.success()


@router.post("/deleteGJFriendRequests20.php")
async def delete_friend_requests(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_friend_requests(form), secret=Secret.COMMON, form=form
    )

    response.unwrap(
        await socials.delete_friend_requests(
            ctx, session, request.target_account_ids, is_sender=request.is_sender
        )
    )

    return response.success()


@router.post("/readGJFriendRequest20.php")
async def read_friend_request(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_read_friend_request(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await socials.read_friend_request(ctx, session, request.request_id))

    return response.success()


@router.post("/getGJFriendRequests20.php")
async def friend_requests(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_friend_requests(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(
        await socials.list_friend_requests(
            ctx, session, request.page, sent=request.sent
        )
    )

    if not payload.requests:
        return response.text(responses.NO_ENTRIES)

    return response.text(
        responses.serialise_friend_requests(payload.requests, payload.page)
    )


@router.post("/removeGJFriend20.php")
async def remove_friend(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_block(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(
        await socials.remove_friend(ctx, session, request.target_account_id)
    )

    return response.success()


@router.post("/blockGJUser20.php")
async def block(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_block(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await socials.block(ctx, session, request.target_account_id))

    return response.success()


@router.post("/unblockGJUser20.php")
async def unblock(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_block(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await socials.unblock(ctx, session, request.target_account_id))

    return response.success()


@router.post("/getGJUserList20.php")
async def user_list(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_user_list(form), secret=Secret.COMMON, form=form
    )
    entries = response.unwrap(await socials.user_list(ctx, session, request.list_type))

    if not entries:
        return response.text(responses.NO_ENTRIES)

    return response.text(responses.serialise_user_list(entries))


@router.post("/uploadGJMessage20.php")
async def send_message(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_send_message(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(await socials.send_message(ctx, session, request))

    return response.success()


@router.post("/getGJMessages20.php")
async def messages(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_messages(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(
        await socials.list_messages(ctx, session, request.page, sent=request.sent)
    )

    if not payload.messages:
        return response.text(responses.NO_ENTRIES)

    return response.text(responses.serialise_messages(payload.messages, payload.page))


@router.post("/downloadGJMessage20.php")
async def download_message(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_download_message(form), secret=Secret.COMMON, form=form
    )

    message = response.unwrap(
        await socials.download_message(
            ctx, session, request.message_id, is_sender=request.is_sender
        )
    )

    return response.text(responses.serialise_message_download(message))


@router.post("/deleteGJMessages20.php")
async def delete_messages(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_messages(form), secret=Secret.COMMON, form=form
    )

    response.unwrap(
        await socials.delete_messages(
            ctx, session, request.message_ids, is_sender=request.is_sender
        )
    )

    return response.success()
