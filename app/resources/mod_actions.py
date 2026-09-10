import json
from enum import StrEnum

from app.adapters.mysql import ImplementsMySQL


class ModTarget(StrEnum):
    USER = "user"
    LEVEL = "level"
    LEVEL_LIST = "level_list"
    COMMENT = "comment"
    ACCOUNT_COMMENT = "account_comment"
    SONG = "song"
    TIMELY_LEVEL = "timely_level"
    MAP_PACK = "map_pack"
    GAUNTLET = "gauntlet"
    QUEST = "quest"
    SECRET_REWARD = "secret_reward"
    ROLE = "role"


class ModActionRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql

    async def create(
        self,
        user_id: int,
        action: str,
        target_type: ModTarget,
        target_id: int,
        details: dict[str, object] | None = None,
    ) -> int:
        result = await self._mysql.execute(
            "INSERT INTO mod_actions (user_id, action, target_type, target_id, "
            "details) "
            "VALUES (%(user)s, %(action)s, %(type)s, %(target)s, %(details)s)",
            {
                "user": user_id,
                "action": action,
                "type": target_type.value,
                "target": target_id,
                "details": None if details is None else json.dumps(details),
            },
        )

        return result.last_row_id
