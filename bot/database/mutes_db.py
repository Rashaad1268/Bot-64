import logging, datetime, sys, typing, asyncio, asyncpg
from discord import Member
from traceback import print_exc, format_exc


log = logging.getLogger(__name__)


class Mutes:
    def __init__(self, bot):
        self.bot = bot

    async def __create_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS Muted_members(
                Id SERIAL PRIMARY KEY,
                Time timestamp,
                Member_username VARCHAR(45),
                Member_id bigint UNIQUE,
                Expiry timestamp
            )
                """

        try:
            await self.bot.db.execute(query)
            log.info("Created new Muted_members table")

        except Exception as e:
            log.exception(format_exc())

    async def everything(self):
        return await self.bot.db.fetch("SELECT * FROM Muted_members")

    async def add_member(self, target: Member, expire: typing.Optional[str] = None):
        log.debug(f"Adding {str(target)} to muted members table")
        time = datetime.datetime.utcnow()
        query = "INSERT INTO Muted_Members (Time, Member_username, Member_id, Expiry) VALUES($1, $2, $3, $4) RETURNING Id"

        try:
            return await self.bot.db.fetchval(query, time, str(target), target.id, expire)

        except asyncpg.UndefinedTableError:
            log.debug("Table Muted_members does not exist, Creating table")
            await self.__create_table()
            try:
                return await self.bot.db.fetchval(query, time, str(target), target.id, expire)

            except asyncpg.UniqueViolationError:
                query = "UPDATE Muted_members SET Expiry=$1 WHERE Member_id=$2 RETURNING Id"
                await self.bot.db.execute(query, expire, target.id)
                log.debug(
                    f"Member {str(target)} is aldready in muted members, Updating column..."
                )
                return await self.bot.db.fetchval(query, expire, target.id)

        except asyncpg.UniqueViolationError:
            "Updates the column if a dupicate value is found"
            query = "UPDATE Muted_members SET Expiry=$1 WHERE Member_id=$2 RETURNING Id"
            return await self.bot.db.fetchval(query, expire, target.id)
            # await self.bot.db.execute(query, expire, target.id)
            log.debug(
                f"Member {str(target)} is aldready in muted members, Updating column..."
            )

    async def all_member_ids(self):
        query = "SELECT Member_id FROM Muted_Members"

        try:
            muted_member_ids = await self.bot.db.fetch(query)

        except asyncpg.UndefinedTableError:
            log.debug("Table Muted_members does not exist...\nCreating one")
            await self.__create_table()
            muted_member_ids = None  # Just created the table

        return muted_member_ids

    async def remove_member(self, member: Member):
        query = "DELETE FROM Muted_members WHERE Member_id=$1"

        try:
            await self.bot.db.execute(query, member.id)

        except asyncpg.UndefinedTableError:
            await self.__create_table()
            log.info("Table muted_members does not exists, Creating table")

        except Exception as e:
            log.exception(format_exc())

    async def get_infraction(self, member: Member):
        query = "SELECT * FROM Muted_members WHERE Member_id=$1"
        return await self.bot.db.fetchrow(query, member.id)
