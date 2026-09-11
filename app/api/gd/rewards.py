from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret
from poltergeist_core.services import rewards

from app.api.gd import response
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction

router = APIRouter()


@router.post("/getGJRewards.php")
async def chests(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_rewards(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(await rewards.rewards(ctx, session, request.reward_type))

    return response.text(
        responses.serialise_rewards(
            session.user.id,
            request.chk,
            request.client.udid,
            session.user.id,
            payload.small.seconds_left,
            payload.small.contents,
            payload.small.count,
            payload.large.seconds_left,
            payload.large.contents,
            payload.large.count,
            payload.reward_type,
        )
    )


@router.post("/getGJChallenges.php")
async def challenges(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_challenges(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(await rewards.challenges(ctx, session))

    return response.text(
        responses.serialise_challenges(
            session.user.id,
            request.chk,
            request.client.udid,
            session.user.id,
            payload.seconds_left,
            payload.quests,
        )
    )


@router.post("/getGJSecretReward.php")
async def secret_reward(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(
        requests.parse_secret_reward(form), secret=Secret.COMMON, form=form
    )
    payload = response.unwrap(
        await rewards.secret_reward(ctx, session, request.reward_key)
    )

    return response.text(
        responses.serialise_secret_reward(
            request.chk, payload.reward_id, payload.chest_type, payload.rewards
        )
    )
