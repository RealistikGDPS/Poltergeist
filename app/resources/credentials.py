from app.adapters.mysql import ImplementsMySQL
from app.resources._common import Model


class UserCredential(Model):
    user_id: int
    gjp2_bcrypt: str


class CredentialRepository:
    __slots__ = ("_mysql",)

    def __init__(self, mysql: ImplementsMySQL) -> None:
        self._mysql = mysql

    async def find_by_user_id(self, user_id: int) -> UserCredential | None:
        row = await self._mysql.fetch_one(
            "SELECT user_id, gjp2_bcrypt FROM user_credentials WHERE user_id = %(id)s",
            {"id": user_id},
        )

        return None if row is None else UserCredential.model_validate(row)

    async def upsert(self, user_id: int, gjp2_bcrypt: str) -> None:
        await self._mysql.execute(
            "INSERT INTO user_credentials (user_id, gjp2_bcrypt) "
            "VALUES (%(id)s, %(hash)s) "
            "ON DUPLICATE KEY UPDATE gjp2_bcrypt = VALUES(gjp2_bcrypt)",
            {"id": user_id, "hash": gjp2_bcrypt},
        )
