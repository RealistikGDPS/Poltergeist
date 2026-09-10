from gdformat.enums import Platform

from app.adapters.mysql import ImplementsMySQL
from app.utilities import clock


class DeviceRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql

    async def upsert(self, user_id: int, udid: str, platform: Platform) -> None:
        await self._mysql.execute(
            "INSERT INTO user_devices (user_id, udid, platform) "
            "VALUES (%(id)s, %(udid)s, %(platform)s) ON DUPLICATE KEY UPDATE "
            "platform = VALUES(platform), last_seen_at = %(now)s",
            {
                "id": user_id,
                "udid": udid,
                "platform": int(platform),
                "now": clock.now(),
            },
        )

    async def list_user_ids_by_udid(self, udid: str) -> list[int]:
        rows = await self._mysql.fetch_all(
            "SELECT user_id FROM user_devices WHERE udid = %(udid)s",
            {"udid": udid},
        )

        return [int(row["user_id"]) for row in rows]
