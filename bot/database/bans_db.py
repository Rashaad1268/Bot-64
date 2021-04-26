import datetime, typing, asyncpg, logging

from discord import Member
from traceback import format_exc
from bot.constants import Postgress

log = logging.getLogger(__name__)


class Bans:
    def __init__(self, bot):
        self.bot = bot

    async def __create_table(self):
        command = """
                CREATE TABLE IF NOT EXISTS Banned_members(
                    Id SERIAL PRIMARY KEY,
                    Time TIMESTAMP,
                    Member_username varchar,
                    Member_id bigint UNIQUE,
                    Expiry TIMESTAMP
                )"""

        try:
            await self.bot.db.execute(command)
            log.debug("Created new Banned_members table")

        except Exception as e:
            log.exception(format_exc())

    async def everything(self):
        return await self.bot.db.fetch("SELECT * FROM Banned_members")

    async def add_member(self, target: Member, expire: typing.Optional[str] = None):
        log.debug(f"Adding {str(target)} to banned members table")
        time = datetime.datetime.utcnow()
        command = "INSERT INTO Banned_members (Time, Member_username, Member_id, Expiry) VALUES($1, $2, $3, $4) RETURNING Id"

        try:
            await self.bot.db.execute(command, time, str(target), target.id, expire)
            return await self.bot.db.fetchval(
                command, time, str(target), target.id, expire
            )

        except asyncpg.UndefinedTableError:
            log.debug("Table Banned_members does not exist\nCreateing table...")
            await self.__create_table()
            try:
                await self.bot.db.execute(command, time, str(target), target.id, expire)
                return await self.bot.db.fetchval(
                    command, time, str(target), target.id, expire
                )

            except asyncpg.UniqueViolationError:
                command = "UPDATE Banned_members SET Expiry=$1 WHERE Member_id=$2 RETURNING Id"
                await self.bot.db.execute(command, expire, target.id)
                log.debug(
                    f"Member {str(target)} aldready in banned members. Updating column."
                )
                return await self.bot.db.fetchval(command, expire, target.id)

        except asyncpg.UniqueViolationError:
            "Updates the column if a dupicate value is found"
            command = (
                "UPDATE Banned_members SET Expiry=$1 WHERE Member_id=$2 RETURNING Id"
            )
            await self.bot.db.execute(command, expire, target.id)
            log.debug(
                f"Member {str(target)} aldready in banned members. Updating column."
            )
            return await self.bot.db.fetchval(command, expire, target.id)

    async def all_member_ids(self):

        command = "SELECT Member_id FROM Banned_Members"

        try:
            member_ids = await self.bot.db.fetch(command)

        except asyncpg.UndefinedTableError:
            log.debug("Table Banned_members does not exist...\nCreating table...")
            await self.__create_table()
            muted_member_ids = None  # Just created the table

        return member_ids

    async def remove_member(self, target: Member):
        command = "DELETE FROM Banned_members WHERE Member_id = $1"

        try:
            await self.bot.db.execute(command, target.id)

        except Exception as e:
            log.exception(format_exc())
