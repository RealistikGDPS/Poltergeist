"""Imports a 2.1-era Ognisko database and storage volume into Poltergeist.
Ids are preserved. Run with the application's environment plus IMPORT_MYSQL_*
and IMPORT_STORAGE_PATH against an empty, migrated target database."""

import asyncio
import hashlib
import json
import os
import shutil
from collections.abc import Mapping
from datetime import datetime
from enum import IntFlag
from pathlib import Path
from typing import Any

from poltergeist_core.adapters.mysql import ImplementsMySQL
from poltergeist_core.adapters.mysql import MySQLPool
from poltergeist_core.utilities import clock
from poltergeist_core.utilities import logging

type Row = Mapping[str, Any]

logger = logging.get_logger(__name__)

_DEFAULT_ROLE = 1
_MODERATOR_ROLE = 2
_ELDER_ROLE = 3
_LEADERBOARD_ROLE = 4
_ADMIN_ROLE = 5
_LEVEL_COMMENT_MAX = 100
_ACCOUNT_COMMENT_MAX = 140
_STARS_DEMON = 10
_DIFFICULTY_STEP = 10
_BYTES_PER_MB = 1_048_576
_TIMELY_DURATIONS = {0: 86_400, 1: 604_800}
_OLD_DEMON_TIERS = {3: 6, 4: 7, 0: 8, 5: 9, 6: 10}
_CHEST_SHARDS = (
    ("fire_shards", 1),
    ("ice_shards", 2),
    ("poison_shards", 3),
    ("shadow_shards", 4),
    ("lava_shards", 5),
)


class OldPrivileges(IntFlag):
    USER_AUTHENTICATE = 1 << 0
    USER_STAR_LEADERBOARD_PUBLIC = 1 << 2
    USER_CREATOR_LEADERBOARD_PUBLIC = 1 << 3
    USER_DISPLAY_ELDER_BADGE = 1 << 4
    USER_DISPLAY_MOD_BADGE = 1 << 5
    USER_REQUEST_ELDER = 1 << 6
    USER_REQUEST_MODERATOR = 1 << 7
    USER_MODIFY_PRIVILEGES = 1 << 9
    LEVEL_UPLOAD = 1 << 12
    LEVEL_RATE_STARS = 1 << 16
    COMMENTS_POST = 1 << 23


def _roles(privileges: OldPrivileges) -> list[int]:
    roles = [_DEFAULT_ROLE]

    if privileges & OldPrivileges.USER_MODIFY_PRIVILEGES:
        roles.append(_ADMIN_ROLE)

    if privileges & (
        OldPrivileges.LEVEL_RATE_STARS
        | OldPrivileges.USER_DISPLAY_ELDER_BADGE
        | OldPrivileges.USER_REQUEST_ELDER
    ):
        roles.append(_ELDER_ROLE)
    elif privileges & (
        OldPrivileges.USER_DISPLAY_MOD_BADGE | OldPrivileges.USER_REQUEST_MODERATOR
    ):
        roles.append(_MODERATOR_ROLE)

    return roles


def _bans(privileges: OldPrivileges) -> list[str]:
    bans = []

    if not privileges & OldPrivileges.USER_AUTHENTICATE:
        bans.append("account")

    if not privileges & OldPrivileges.COMMENTS_POST:
        bans.append("comment")

    if not privileges & OldPrivileges.LEVEL_UPLOAD:
        bans.append("upload")

    if not privileges & OldPrivileges.USER_STAR_LEADERBOARD_PUBLIC:
        bans.append("leaderboard")

    if not privileges & OldPrivileges.USER_CREATOR_LEADERBOARD_PUBLIC:
        bans.append("creator")

    return bans


def _colour(text: str) -> int | None:
    parts = text.split(",")

    if len(parts) != 3 or not all(part.isdecimal() for part in parts):
        return None

    red, green, blue = (int(part) for part in parts)

    if (red, green, blue) == (0, 0, 0):
        return None

    return (red << 16) | (green << 8) | blue


def _icon(value: int) -> int:
    return value if value > 0 else 1


def _difficulty(stars: int, numerator: int, demon: int | None) -> int:
    if stars == _STARS_DEMON:
        return _OLD_DEMON_TIERS.get(demon if demon is not None else 0, 8)

    if stars == 1:
        return 0

    if 2 <= stars <= 9:
        return {2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}[stars]

    if numerator > 0:
        return min(numerator // _DIFFICULTY_STEP, 5)

    if demon is not None:
        return _OLD_DEMON_TIERS.get(demon, 8)

    return -1


def _rating(search_flags: int) -> int:
    if search_flags & 16:
        return 3

    if search_flags & 8:
        return 2

    if search_flags & 1:
        return 1

    return 0


def _json_ids(value: object) -> list[int]:
    if value is None:
        return []

    parsed = json.loads(value) if isinstance(value, str | bytes) else value

    if not isinstance(parsed, list):
        return []

    return [int(item) for item in parsed if isinstance(item, int)]


def _deleted_at(flag: object) -> datetime | None:
    return clock.now() if flag else None


class Importer:
    def __init__(
        self,
        old: ImplementsMySQL,
        new: ImplementsMySQL,
        old_storage: Path,
        new_storage: Path,
    ) -> None:
        self._old = old
        self._new = new
        self._old_storage = old_storage
        self._new_storage = new_storage
        self._user_ids: set[int] = set()
        self._level_ids: set[int] = set()
        self._song_ids: set[int] = set()
        self._originals: dict[int, int] = {}

    async def _users(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM users ORDER BY id")
        credentials = {
            int(row["user_id"]): row
            for row in await self._old.fetch_all(
                "SELECT user_id, version, value FROM user_credentials ORDER BY id"
            )
        }

        for row in rows:
            user_id = int(row["id"])
            self._user_ids.add(user_id)
            privileges = OldPrivileges(int.from_bytes(row["privileges"], "little"))

            await self._new.execute(
                "INSERT INTO users (id, username, email, comment_colour, "
                "message_privacy, friend_request_privacy, comment_history_privacy, "
                "youtube, twitter, twitch, registered_at) VALUES (%(id)s, %(name)s, "
                "%(email)s, %(colour)s, %(messages)s, %(friends)s, %(history)s, "
                "%(youtube)s, %(twitter)s, %(twitch)s, %(registered)s)",
                {
                    "id": user_id,
                    "name": row["username"],
                    "email": str(row["email"]).strip().lower(),
                    "colour": _colour(str(row["comment_colour"])),
                    "messages": min(int(row["message_privacy"]), 2),
                    "friends": 1 if int(row["friend_privacy"]) == 2 else 0,
                    "history": min(int(row["comment_privacy"]), 2),
                    "youtube": (row["youtube_name"] or "")[:64],
                    "twitter": (row["twitter_name"] or "")[:64],
                    "twitch": (row["twitch_name"] or "")[:64],
                    "registered": row["register_ts"],
                },
            )
            glow_colour = int(row["glow_colour"])

            await self._new.execute(
                "INSERT INTO user_stats (user_id, stars, moons, demons, diamonds, "
                "secret_coins, user_coins, icon_type, colour1, colour2, colour3, glow, "
                "icon_cube, icon_ship, icon_ball, icon_ufo, icon_wave, icon_robot, "
                "icon_spider, icon_swing, icon_jetpack, icon_explosion) VALUES "
                "(%(id)s, %(stars)s, %(moons)s, %(demons)s, %(diamonds)s, %(coins)s, "
                "%(user_coins)s, %(icon_type)s, %(c1)s, %(c2)s, %(c3)s, %(glow)s, "
                "%(cube)s, %(ship)s, %(ball)s, %(ufo)s, %(wave)s, %(robot)s, "
                "%(spider)s, %(swing)s, %(jetpack)s, %(explosion)s)",
                {
                    "id": user_id,
                    "stars": row["stars"],
                    "moons": row["moons"],
                    "demons": row["demons"],
                    "diamonds": row["diamonds"],
                    "coins": row["coins"],
                    "user_coins": row["user_coins"],
                    "icon_type": min(int(row["display_type"]), 8),
                    "c1": row["primary_colour"],
                    "c2": row["secondary_colour"],
                    "c3": glow_colour if glow_colour != 0 else -1,
                    "glow": bool(row["glow"]),
                    "cube": _icon(int(row["icon"])),
                    "ship": _icon(int(row["ship"])),
                    "ball": _icon(int(row["ball"])),
                    "ufo": _icon(int(row["ufo"])),
                    "wave": _icon(int(row["wave"])),
                    "robot": _icon(int(row["robot"])),
                    "spider": _icon(int(row["spider"])),
                    "swing": _icon(int(row["swing_copter"])),
                    "jetpack": _icon(int(row["jetpack"])),
                    "explosion": _icon(int(row["explosion"])),
                },
            )
            credential = credentials.get(user_id)

            if credential is not None:
                is_gjp2 = int(credential["version"]) == 2

                await self._new.execute(
                    "INSERT INTO user_credentials (user_id, gjp2_bcrypt, "
                    "legacy_password_bcrypt) VALUES (%(id)s, %(gjp2)s, %(legacy)s)",
                    {
                        "id": user_id,
                        "gjp2": credential["value"] if is_gjp2 else None,
                        "legacy": None if is_gjp2 else credential["value"],
                    },
                )

            for role_id in _roles(privileges):
                await self._new.execute(
                    "INSERT INTO user_roles (user_id, role_id, created_at) "
                    "VALUES (%(user)s, %(role)s, %(at)s)",
                    {"user": user_id, "role": role_id, "at": row["register_ts"]},
                )

            for ban_type in _bans(privileges):
                await self._new.execute(
                    "INSERT INTO user_bans (user_id, type, reason) "
                    "VALUES (%(user)s, %(type)s, 'Imported from the previous server.')",
                    {"user": user_id, "type": ban_type},
                )

        logger.info("Imported users.", extra={"count": len(rows)})

    async def _songs(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM songs ORDER BY id")
        artists_by_name: dict[str, int] = {}
        seen_artist_ids: set[int] = set()

        for row in rows:
            song_id = int(row["id"])
            source = int(row["source"])
            name = str(row["author"]).strip() or "Unknown"

            if source == 2:
                artist_id = artists_by_name.get(name.lower())

                if artist_id is None:
                    result = await self._new.execute(
                        "INSERT INTO artists (name) VALUES (%(name)s)",
                        {"name": name[:64]},
                    )
                    artist_id = result.last_row_id
                    artists_by_name[name.lower()] = artist_id
            else:
                artist_id = int(row["author_id"])

                if artist_id not in seen_artist_ids:
                    seen_artist_ids.add(artist_id)

                    await self._new.execute(
                        "INSERT INTO artists (id, name, youtube_channel) "
                        "VALUES (%(id)s, %(name)s, %(youtube)s)",
                        {
                            "id": artist_id,
                            "name": name[:64],
                            "youtube": (row["author_youtube"] or "")[:64],
                        },
                    )

            self._song_ids.add(song_id)

            await self._new.execute(
                "INSERT INTO songs (id, name, artist_id, size_bytes, url, source, "
                "disabled_at) VALUES (%(id)s, %(name)s, %(artist)s, %(size)s, %(url)s, "
                "%(source)s, %(disabled)s)",
                {
                    "id": song_id,
                    "name": str(row["name"])[:128],
                    "artist": artist_id,
                    "size": int(float(row["size"]) * _BYTES_PER_MB),
                    "url": str(row["download_url"])[:512],
                    "source": "custom" if source == 2 else "newgrounds",
                    "disabled": _deleted_at(row["blocked"]),
                },
            )

        logger.info("Imported songs.", extra={"count": len(rows)})

    async def _levels(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM levels ORDER BY id")
        skipped = 0
        (self._new_storage / "levels").mkdir(parents=True, exist_ok=True)

        for row in rows:
            level_id = int(row["id"])
            user_id = int(row["user_id"])
            source = self._old_storage / "levels" / str(level_id)

            if user_id not in self._user_ids or not source.is_file():
                skipped += 1

                continue

            self._level_ids.add(level_id)
            stars = int(row["stars"])
            custom_song = row["custom_song_id"]

            if row["original_id"]:
                self._originals[level_id] = int(row["original_id"])

            await self._new.execute(
                "INSERT INTO levels (id, user_id, name, description, version, length, "
                "official_song_id, custom_song_id, game_version, binary_version, "
                "visibility, two_player, low_detail_mode, original_id, copyable, "
                "object_count, coins, coins_verified, requested_stars, editor_seconds, "
                "downloads, likes, difficulty, stars, feature_order, rating, rated_at, "
                "update_locked, uploaded_at, updated_at, deleted_at) VALUES (%(id)s, "
                "%(user)s, %(name)s, %(description)s, %(version)s, %(length)s, "
                "%(official)s, %(custom)s, %(game)s, %(binary)s, %(visibility)s, "
                "%(two_player)s, %(ldm)s, NULL, FALSE, %(objects)s, %(coins)s, "
                "%(verified)s, %(requested)s, %(editor)s, %(downloads)s, %(likes)s, "
                "%(difficulty)s, %(stars)s, %(feature)s, %(rating)s, %(rated_at)s, "
                "%(locked)s, %(uploaded)s, %(updated)s, %(deleted)s)",
                {
                    "id": level_id,
                    "user": user_id,
                    "name": str(row["name"])[:32],
                    "description": str(row["description"])[:300],
                    "version": max(int(row["version"]), 1),
                    "length": min(int(row["length"]), 5),
                    "official": int(row["official_song_id"] or 0),
                    "custom": int(custom_song) if custom_song else None,
                    "game": row["game_version"],
                    "binary": row["binary_version"],
                    "visibility": 2
                    if int(row["publicity"]) == 1
                    else int(row["publicity"]),
                    "two_player": bool(row["two_player"]),
                    "ldm": bool(row["low_detail_mode"]),
                    "objects": row["object_count"],
                    "coins": min(int(row["coins"]), 3),
                    "verified": bool(row["coins_verified"]),
                    "requested": min(int(row["requested_stars"]), 10),
                    "editor": row["building_time"],
                    "downloads": row["downloads"],
                    "likes": row["likes"],
                    "difficulty": _difficulty(
                        stars, int(row["difficulty"]), row["demon_difficulty"]
                    ),
                    "stars": min(stars, 10),
                    "feature": max(int(row["feature_order"]), 0),
                    "rating": _rating(int(row["search_flags"])),
                    "rated_at": row["update_ts"] if stars > 0 else None,
                    "locked": bool(row["update_locked"]),
                    "uploaded": row["upload_ts"],
                    "updated": row["update_ts"],
                    "deleted": _deleted_at(row["deleted"]),
                },
            )
            data = source.read_bytes()
            shutil.copyfile(source, self._new_storage / "levels" / f"{level_id}.dat")

            await self._new.execute(
                "INSERT INTO level_data (level_id, size_bytes, sha1, extra_string, "
                "song_ids, sfx_ids) VALUES (%(id)s, %(size)s, %(sha1)s, %(extra)s, "
                "%(songs)s, %(sfx)s)",
                {
                    "id": level_id,
                    "size": len(data),
                    "sha1": hashlib.sha1(data).digest(),
                    "extra": str(row["render_str"])[:1024],
                    "songs": json.dumps(_json_ids(row["song_ids"])),
                    "sfx": json.dumps(_json_ids(row["sfx_ids"])),
                },
            )

        await self._new.execute(
            "UPDATE levels SET original_id = NULL WHERE original_id IS NOT NULL "
            "AND original_id NOT IN (SELECT id FROM (SELECT id FROM levels) l)"
        )
        logger.info(
            "Imported levels.", extra={"count": len(rows) - skipped, "skipped": skipped}
        )

    async def _comments(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM level_comments ORDER BY id")
        imported = 0

        for row in rows:
            if (
                int(row["user_id"]) not in self._user_ids
                or int(row["level_id"]) not in self._level_ids
            ):
                continue

            imported += 1

            await self._new.execute(
                "INSERT INTO comments (id, user_id, level_id, content, percent, likes, "
                "created_at, deleted_at) VALUES (%(id)s, %(user)s, %(level)s, "
                "%(content)s, %(percent)s, %(likes)s, %(at)s, %(deleted)s)",
                {
                    "id": row["id"],
                    "user": row["user_id"],
                    "level": row["level_id"],
                    "content": str(row["content"])[:_LEVEL_COMMENT_MAX],
                    "percent": min(max(int(row["percent"]), 0), 100),
                    "likes": row["likes"],
                    "at": row["post_ts"],
                    "deleted": _deleted_at(row["deleted"]),
                },
            )

        account_rows = await self._old.fetch_all(
            "SELECT * FROM user_comments ORDER BY id"
        )
        account_imported = 0

        for row in account_rows:
            if int(row["user_id"]) not in self._user_ids:
                continue

            account_imported += 1

            await self._new.execute(
                "INSERT INTO account_comments (id, user_id, content, likes, "
                "created_at, deleted_at) VALUES (%(id)s, %(user)s, %(content)s, "
                "%(likes)s, %(at)s, %(deleted)s)",
                {
                    "id": row["id"],
                    "user": row["user_id"],
                    "content": str(row["content"])[:_ACCOUNT_COMMENT_MAX],
                    "likes": row["likes"],
                    "at": row["post_ts"],
                    "deleted": _deleted_at(row["deleted"]),
                },
            )

        logger.info(
            "Imported comments.",
            extra={"level_comments": imported, "account_comments": account_imported},
        )

    async def _likes(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM user_likes ORDER BY id")
        targets = {1: "level", 3: "account_comment"}
        imported = 0

        for row in rows:
            target = targets.get(int(row["target_type"]))

            if target is None or int(row["user_id"]) not in self._user_ids:
                continue

            result = await self._new.execute(
                "INSERT IGNORE INTO likes (user_id, target_type, target_id, is_like) "
                "VALUES (%(user)s, %(type)s, %(target)s, %(like)s)",
                {
                    "user": row["user_id"],
                    "type": target,
                    "target": row["target_id"],
                    "like": int(row["value"]) == 1,
                },
            )
            imported += result.affected_rows

        logger.info("Imported likes.", extra={"count": imported})

    async def _social(self) -> None:
        requests = await self._old.fetch_all(
            "SELECT * FROM friend_requests ORDER BY id"
        )
        imported = 0

        for row in requests:
            if (
                int(row["sender_user_id"]) not in self._user_ids
                or int(row["recipient_user_id"]) not in self._user_ids
            ):
                continue

            result = await self._new.execute(
                "INSERT IGNORE INTO friend_requests (id, sender_user_id, "
                "recipient_user_id, message, created_at, read_at, deleted_at) VALUES "
                "(%(id)s, %(sender)s, %(recipient)s, %(message)s, %(at)s, %(read)s, "
                "%(deleted)s)",
                {
                    "id": row["id"],
                    "sender": row["sender_user_id"],
                    "recipient": row["recipient_user_id"],
                    "message": str(row["message"])[:140],
                    "at": row["post_ts"],
                    "read": row["seen_ts"],
                    "deleted": _deleted_at(row["deleted"]),
                },
            )
            imported += result.affected_rows

        relationships = await self._old.fetch_all(
            "SELECT * FROM user_relationships ORDER BY id"
        )
        friendships = 0
        blocks = 0

        for row in relationships:
            user_id = int(row["user_id"])
            target_id = int(row["target_user_id"])

            if (
                user_id not in self._user_ids
                or target_id not in self._user_ids
                or user_id == target_id
            ):
                continue

            if int(row["relationship_type"]) == 0:
                result = await self._new.execute(
                    "INSERT IGNORE INTO friendships (user_id, friend_user_id, "
                    "created_at, seen_at, deleted_at) VALUES (%(user)s, %(friend)s, "
                    "%(at)s, %(seen)s, %(deleted)s)",
                    {
                        "user": user_id,
                        "friend": target_id,
                        "at": row["post_ts"],
                        "seen": row["seen_ts"] or row["post_ts"],
                        "deleted": _deleted_at(row["deleted"]),
                    },
                )
                friendships += result.affected_rows
            else:
                result = await self._new.execute(
                    "INSERT IGNORE INTO user_blocks (user_id, blocked_user_id, "
                    "created_at, deleted_at) VALUES (%(user)s, %(blocked)s, %(at)s, "
                    "%(deleted)s)",
                    {
                        "user": user_id,
                        "blocked": target_id,
                        "at": row["post_ts"],
                        "deleted": _deleted_at(row["deleted"]),
                    },
                )
                blocks += result.affected_rows

        messages = await self._old.fetch_all("SELECT * FROM messages ORDER BY id")
        message_count = 0

        for row in messages:
            if (
                int(row["sender_user_id"]) not in self._user_ids
                or int(row["recipient_user_id"]) not in self._user_ids
            ):
                continue

            message_count += 1
            deleted = _deleted_at(row["deleted"])

            await self._new.execute(
                "INSERT INTO messages (id, sender_user_id, recipient_user_id, subject, "
                "body, created_at, read_at, sender_deleted_at, recipient_deleted_at) "
                "VALUES (%(id)s, %(sender)s, %(recipient)s, %(subject)s, %(body)s, "
                "%(at)s, %(read)s, %(sender_deleted)s, %(recipient_deleted)s)",
                {
                    "id": row["id"],
                    "sender": row["sender_user_id"],
                    "recipient": row["recipient_user_id"],
                    "subject": str(row["subject"] or "")[:35],
                    "body": str(row["content"] or "")[:200],
                    "at": row["post_ts"],
                    "read": row["seen_ts"],
                    "sender_deleted": deleted or _deleted_at(row["sender_deleted"]),
                    "recipient_deleted": deleted
                    or _deleted_at(row["recipient_deleted"]),
                },
            )

        logger.info(
            "Imported social data.",
            extra={
                "friend_requests": imported,
                "friendships": friendships,
                "blocks": blocks,
                "messages": message_count,
            },
        )

    async def _chests(self) -> None:
        rows = await self._old.fetch_all("SELECT * FROM daily_chests ORDER BY id")
        imported = 0

        for row in rows:
            if int(row["user_id"]) not in self._user_ids:
                continue

            imported += 1
            shard = next(
                (code for column, code in _CHEST_SHARDS if int(row[column]) > 0), 0
            )

            await self._new.execute(
                "INSERT INTO chest_claims (user_id, chest_type, orbs, diamonds, shard, "
                "demon_keys, claimed_at) VALUES (%(user)s, %(type)s, %(orbs)s, "
                "%(diamonds)s, %(shard)s, %(keys)s, %(at)s)",
                {
                    "user": row["user_id"],
                    "type": int(row["type"]) + 1,
                    "orbs": max(int(row["mana"]), 0),
                    "diamonds": max(int(row["diamonds"]), 0),
                    "shard": shard,
                    "keys": max(int(row["demon_keys"]), 0),
                    "at": row["claimed_ts"],
                },
            )

        logger.info("Imported chest claims.", extra={"count": imported})

    async def _timely(self) -> None:
        rows = await self._old.fetch_all(
            "SELECT * FROM level_schedule ORDER BY type, start_time"
        )
        sequences: dict[int, int] = {}
        imported = 0

        for row in rows:
            timely_type = int(row["type"])

            if (
                timely_type not in _TIMELY_DURATIONS
                or int(row["level_id"]) not in self._level_ids
            ):
                continue

            sequences[timely_type] = sequences.get(timely_type, 0) + 1
            imported += 1
            scheduled_by = row["scheduled_by_id"]

            await self._new.execute(
                "INSERT INTO timely_levels (type, sequence, level_id, starts_at, "
                "ends_at, scheduled_by_user_id) VALUES (%(type)s, %(sequence)s, "
                "%(level)s, %(starts)s, %(ends)s, %(by)s)",
                {
                    "type": timely_type,
                    "sequence": sequences[timely_type],
                    "level": row["level_id"],
                    "starts": row["start_time"],
                    "ends": row["end_time"],
                    "by": scheduled_by if scheduled_by in self._user_ids else None,
                },
            )

        logger.info("Imported timely levels.", extra={"count": imported})

    async def _saves(self) -> None:
        saves = self._old_storage / "saves"
        imported = 0

        for path in saves.iterdir():
            if not path.name.isdecimal() or int(path.name) not in self._user_ids:
                continue

            parts = path.read_bytes().split(b";")

            if len(parts) < 2:
                continue

            user_id = int(path.name)
            versions = [part for part in parts[2:] if part.isdigit()]
            game_version = int(versions[0]) if len(versions) >= 2 else 0
            binary_version = int(versions[-1]) if versions else 0
            target = self._new_storage / "saves" / str(user_id)
            target.mkdir(parents=True, exist_ok=True)
            (target / "game_manager.dat").write_bytes(parts[0])
            (target / "local_levels.dat").write_bytes(parts[1])
            imported += 1

            await self._new.execute(
                "INSERT INTO user_saves (user_id, game_version, binary_version, "
                "game_manager_bytes, local_levels_bytes, saved_at) VALUES (%(id)s, "
                "%(game)s, %(binary)s, %(manager)s, %(levels)s, %(at)s)",
                {
                    "id": user_id,
                    "game": min(game_version, 255),
                    "binary": min(binary_version, 255),
                    "manager": len(parts[0]),
                    "levels": len(parts[1]),
                    "at": datetime.fromtimestamp(path.stat().st_mtime).replace(
                        microsecond=0
                    ),
                },
            )

        logger.info("Imported saves.", extra={"count": imported})

    async def _creator_points(self) -> None:
        await self._new.execute(
            "UPDATE user_stats s SET creator_points = (SELECT COALESCE(SUM((stars > 0) "
            "+ (feature_order > 0) + (rating > 0)), 0) FROM levels l "
            "WHERE l.user_id = s.user_id AND l.deleted_at IS NULL)"
        )
        logger.info("Recomputed creator points.")

    async def run(self) -> None:
        await self._users()
        await self._songs()
        await self._levels()
        await self._comments()
        await self._likes()
        await self._social()
        await self._chests()
        await self._timely()
        await self._saves()
        await self._creator_points()


def _pool(prefix: str) -> MySQLPool:
    return MySQLPool(
        host=os.environ[f"{prefix}_HOST"],
        port=int(os.environ[f"{prefix}_TCP_PORT"]),
        user=os.environ[f"{prefix}_USER"],
        password=os.environ[f"{prefix}_PASSWORD"],
        database=os.environ[f"{prefix}_DATABASE"],
        pool_min=1,
        pool_max=2,
    )


async def main() -> None:
    # The tool's own inputs are read here; the application settings module
    # would otherwise require them for every component.
    old = _pool("IMPORT_MYSQL")
    new = _pool("MYSQL")
    old_storage = Path(os.environ["IMPORT_STORAGE_PATH"])
    new_storage = Path(os.environ["APP_STORAGE_PATH"])
    await old.connect()
    await new.connect()

    async with new.transaction() as transaction:
        await Importer(old, transaction, old_storage, new_storage).run()

    await old.disconnect()
    await new.disconnect()
    logger.info("Import finished.")


if __name__ == "__main__":
    logging.configure_from_yaml()
    asyncio.run(main())
