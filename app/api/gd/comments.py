from fastapi import APIRouter
from fastapi import Response
from gdformat import codes
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret
from poltergeist_core.services import comments

from app.api.gd import response
from app.api.gd.context import RequiresContext
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction

router = APIRouter()

# A permanent ban is shown as a very long temporary one so the reason is visible.
_PERMANENT_SECONDS = 10 * 365 * 86_400


def _outcome(outcome: comments.UploadOutcome) -> Response:
    if outcome.ban is not None:
        seconds = outcome.ban.seconds_left

        if seconds is None:
            seconds = _PERMANENT_SECONDS

        return response.text(
            responses.serialise_comment_ban(seconds, outcome.ban.reason)
        )

    if outcome.reply is not None:
        return response.text(responses.serialise_comment_ban(0, outcome.reply))

    return response.success()


@router.post("/uploadGJComment21.php")
async def upload_level_comment(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_upload_comment(form), secret=Secret.COMMON, form=form
    )
    outcome = response.unwrap(
        await comments.upload_level_comment(ctx, session, request)
    )

    return _outcome(outcome)


@router.post("/deleteGJComment20.php")
async def delete_level_comment(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_comment(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(
        await comments.delete_level_comment(ctx, session, request.comment_id)
    )

    return response.success()


@router.post("/getGJComments21.php")
async def level_comments(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_level_comments(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(
        await comments.list_level_comments(
            ctx, request.level_id, request.mode, request.page, request.count
        )
    )

    if not payload.comments:
        return response.code(codes.CommentError.NONE_FOUND)

    return response.text(
        responses.serialise_level_comments(payload.comments, payload.page)
    )


@router.post("/getGJCommentHistory.php")
async def comment_history(
    form: RequiresForm, session: RequiresSession, ctx: RequiresContext
) -> Response:
    request = response.parse(
        requests.parse_comment_history(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(
        await comments.comment_history(
            ctx, session, request.user_id, request.mode, request.page, request.count
        )
    )

    if not payload.comments:
        return response.code(codes.CommentError.NONE_FOUND)

    return response.text(
        responses.serialise_level_comments(payload.comments, payload.page)
    )


@router.post("/uploadGJAccComment20.php")
async def upload_account_comment(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_upload_account_comment(form), secret=Secret.COMMON, form=form
    )
    outcome = response.unwrap(
        await comments.upload_account_comment(ctx, session, request)
    )

    return _outcome(outcome)


@router.post("/deleteGJAccComment20.php")
async def delete_account_comment(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_delete_account_comment(form), secret=Secret.COMMON, form=form
    )
    response.unwrap(
        await comments.delete_account_comment(ctx, session, request.comment_id)
    )

    return response.success()


# NOTE: On this endpoint the client sends the target's id as `accountID` next
# to its own `gjp2`, so the pair cannot be authenticated. Profile posts are
# public on the official servers too.
@router.post("/getGJAccountComments20.php")
async def account_comments(form: RequiresForm, ctx: RequiresContext) -> Response:
    request = response.parse(
        requests.parse_account_comments(form), secret=Secret.COMMON, form=form
    )

    payload = response.unwrap(
        await comments.list_account_comments(
            ctx, request.account_id, request.page, request.count
        )
    )

    # NOTE: Unlike level comments, an empty profile is an empty page, not -2;
    # the client shows an error dialog for -2 here.
    return response.text(
        responses.serialise_account_comments(payload.comments, payload.page)
    )
