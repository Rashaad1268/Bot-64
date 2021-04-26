import datetime, asyncio, asyncpg, logging
import typing as t

from discord import Member
from traceback import format_exc

log = logging.getLogger(__name__)


class Warns:
    def __init__(self, bot):
        self.bot = bot

    async def __create_table(self):
        query = """
                CREATE TABLE IF NOT EXISTS Warns(
                    Id SERIAL PRIMARY KEY,
                    Member_username varchar,
                    Member_id bigint UNIQUE,
                    Time TIMESTAMP,
                    Reason VARCHAR(255)
                )"""

        await self.bot.db.execute(query)

    async def everything(self):
        return await self.bot.db.execute("SELECT * FROM Warns;")

    async def warn_member(self, target: Member):
        query = "INSERT INTO Warns (Member_username, Member_id, Warn_count) VALUES($1, $2, $3)"

        try:
            await self.bot.db.execute(query, str(target), target.id, 1)

        except asyncpg.UndefinedTableError:
            log.debug("Warns table doesn't exist...\nCreating table...")
            await self.__create_table()

        except asyncpg.UniqueViolationError:
            log.debug(
                f"Member {str(target)} aldready in warns.\nIncreasing his warn count..."
            )
            query = "UPDATE Warns SET Warn_count = Warn_count + 1 WHERE Member_id = $1"
            await self.bot.db.execute(query, target.id)

    async def increase_warn(self, target: Member, increase_by: t.Optional[int] = 1):
        query = "UPDATE Warns SET Warn_count = Warn_count + $1 WHERE Member_id = $2"
        try:
            await self.bot.db.execute(query, target.id)

        except asyncpg.UndefinedTableError:
            log.debug("Warns table doesn't exist...\nCreating table...")
            await self.__create_table()
            await self.warn_member(target)

    async def delete_warn(self, target: Member, reduce_by: t.Optional[int] = 1):
        query = "UPDATE Warns SET Warn_count = Warn_count - $1 WHERE Member_id = $2"
        try:
            await self.bot.db.execute(query, target.id)

        except asyncpg.UndefinedTableError:
            log.debug("Warns table doesn't exist...\nCreating table...")
            await self.__create_table()

    async def get_infraction(self, target: Member):
        return await self.bot.db.fetchrow(
            "SELECT * FROM WARNS WHERE Member_id = $1", target.id
        )
