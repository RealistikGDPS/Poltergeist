from datetime import datetime

from fastapi import APIRouter
from fastapi import Response
from fastapi import status
from gdformat.enums import ChestType
from gdformat.enums import DemonDifficulty
from gdformat.enums import MapPackDifficulty
from gdformat.enums import RewardItem
from gdformat.enums import SendFeature
from gdformat.enums import TimelyType
from pydantic import BaseModel
from pydantic import Field

from app.api.v1 import response
from app.api.v1.context import RequiresAdmin
from app.api.v1.context import RequiresTransaction
from app.resources import BanType
from app.services import auth
from app.services import leaderboards
from app.services import moderation
from app.services import packs
from app.services import roles
from app.services import songs
from app.services import timely

router = APIRouter(dependencies=[])


class SetPasswordRequest(BaseModel):
    password: str = Field(min_length=6, max_length=64)


class AssignRoleRequest(BaseModel):
    role: str
    expires_at: datetime | None = None


class BanRequest(BaseModel):
    type: BanType
    days: int | None = Field(default=None, ge=1)
    reason: str = ""


class RateLevelRequest(BaseModel):
    stars: int = Field(ge=0, le=10)
    feature: SendFeature | None = None
    demon: DemonDifficulty | None = None


class ScheduleTimelyRequest(BaseModel):
    type: TimelyType
    level_id: int


class CreateSongRequest(BaseModel):
    name: str
    artist: str
    url: str
    size_bytes: int = Field(ge=0)


class CreateMapPackRequest(BaseModel):
    name: str
    level_ids: list[int]
    stars: int = Field(ge=0, le=10)
    coins: int = Field(ge=0, le=2)
    difficulty: MapPackDifficulty
    text_colour: int = Field(default=0xFFFFFF, ge=0, le=0xFFFFFF)
    bar_colour: int = Field(default=0xFFFFFF, ge=0, le=0xFFFFFF)


class SetGauntletRequest(BaseModel):
    level_ids: list[int]


class RewardItemRequest(BaseModel):
    item: RewardItem
    amount: int = Field(ge=1)


class CreateSecretRewardRequest(BaseModel):
    key: str
    chest_type: ChestType
    items: list[RewardItemRequest]
    max_claims: int | None = Field(default=None, ge=1)
    expires_at: datetime | None = None


@router.put("/users/{user_id}/password")
async def set_password(
    user_id: int, body: SetPasswordRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    """Also the way accounts imported from the 2.1 server regain access: their
    stored hash cannot be checked against what a 2.2 client sends."""

    response.unwrap(await auth.set_password(ctx, user_id, body.password))

    return response.create({"user_id": user_id})


@router.post("/users/{user_id}/roles")
async def assign_role(
    user_id: int, body: AssignRoleRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    role = response.unwrap(
        await roles.assign(
            ctx,
            actor_user_id=None,
            target_user_id=user_id,
            role_name=body.role,
            expires_at=body.expires_at,
        )
    )

    return response.create(role.model_dump(), status=status.HTTP_201_CREATED)


@router.delete("/users/{user_id}/roles/{role_name}")
async def revoke_role(
    user_id: int, role_name: str, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    role = response.unwrap(
        await roles.revoke(
            ctx, actor_user_id=None, target_user_id=user_id, role_name=role_name
        )
    )

    return response.create(role.model_dump())


@router.post("/users/{user_id}/bans")
async def ban_user(
    user_id: int, body: BanRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    ban_id = response.unwrap(
        await moderation.ban(
            ctx,
            actor_user_id=None,
            target_user_id=user_id,
            ban_type=body.type,
            days=body.days,
            reason=body.reason,
        )
    )

    return response.create({"ban_id": ban_id}, status=status.HTTP_201_CREATED)


@router.delete("/users/{user_id}/bans/{ban_type}")
async def unban_user(
    user_id: int, ban_type: BanType, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    revoked = response.unwrap(
        await moderation.unban(
            ctx, actor_user_id=None, target_user_id=user_id, ban_type=ban_type
        )
    )

    return response.create({"revoked": revoked})


@router.post("/levels/{level_id}/rating")
async def rate_level(
    level_id: int, body: RateLevelRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    level = response.unwrap(
        await moderation.rate_level(
            ctx,
            actor_user_id=None,
            level_id=level_id,
            stars=body.stars,
            feature=body.feature,
            demon=body.demon,
        )
    )

    return response.create(level.model_dump())


@router.post("/timely")
async def schedule_timely(
    body: ScheduleTimelyRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    entry = response.unwrap(
        await timely.schedule(
            ctx, actor_user_id=None, timely_type=body.type, level_id=body.level_id
        )
    )

    return response.create(entry.model_dump(), status=status.HTTP_201_CREATED)


@router.post("/songs")
async def create_song(
    body: CreateSongRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    song = response.unwrap(
        await songs.create_custom(
            ctx,
            name=body.name,
            artist_name=body.artist,
            url=body.url,
            size_bytes=body.size_bytes,
            uploaded_by_user_id=None,
        )
    )

    return response.create(song.model_dump(), status=status.HTTP_201_CREATED)


@router.post("/map-packs")
async def create_map_pack(
    body: CreateMapPackRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    pack_id = response.unwrap(
        await packs.create_map_pack(
            ctx,
            actor_user_id=None,
            name=body.name,
            level_ids=body.level_ids,
            stars=body.stars,
            coins=body.coins,
            difficulty=body.difficulty,
            text_colour=body.text_colour,
            bar_colour=body.bar_colour,
        )
    )

    return response.create({"map_pack_id": pack_id}, status=status.HTTP_201_CREATED)


@router.put("/gauntlets/{gauntlet_id}")
async def set_gauntlet(
    gauntlet_id: int,
    body: SetGauntletRequest,
    ctx: RequiresTransaction,
    _: RequiresAdmin,
) -> Response:
    response.unwrap(
        await packs.set_gauntlet(
            ctx, actor_user_id=None, gauntlet_id=gauntlet_id, level_ids=body.level_ids
        )
    )

    return response.create({"gauntlet_id": gauntlet_id})


@router.post("/secret-rewards")
async def create_secret_reward(
    body: CreateSecretRewardRequest, ctx: RequiresTransaction, _: RequiresAdmin
) -> Response:
    reward_id = await ctx.secret_rewards.create(
        reward_key=body.key.strip().lower(),
        chest_type=body.chest_type,
        max_claims=body.max_claims,
        expires_at=body.expires_at,
    )

    for item in body.items:
        await ctx.secret_rewards.add_item(reward_id, item.item, item.amount)

    return response.create(
        {"secret_reward_id": reward_id}, status=status.HTTP_201_CREATED
    )


@router.post("/leaderboards/rebuild")
async def rebuild_leaderboards(ctx: RequiresTransaction, _: RequiresAdmin) -> Response:
    total = await leaderboards.rebuild(ctx)

    return response.create({"users": total})
