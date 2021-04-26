import asyncpg, asyncio, logging

from .bans_db import Bans
from .mutes_db import Mutes
from .warns import Warns

log = logging.getLogger(__name__)


def create_pg_uri(user, password, database, host, port):
    """This is not even needed..."""
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


class DataBase:
    def __init__(self, bot, pool, loop=None, timeout=60.0):
        self.__bot = bot
        self.mutes = Mutes(self.__bot) # Now this can be used as bot.db.mutes 
        self.bans = Bans(self.__bot)
        self.warns = Warns(self.__bot)

        self.__pool = pool # Need to keep this private so this can be used as bot.db.pool
        self.__loop = loop
        self._timeout = timeout

    @classmethod
    async def create(cls, uri, bot, loop, timeout=60.0):
        pool = await asyncpg.create_pool(uri)

        return cls(bot, pool, loop, timeout)

    async def execute(self, query, *args):
        async with self.__pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=self._timeout)

    async def fetch(self, query, *args):
        async with self.__pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=self._timeout)

    async def fetchrow(self, query, *args):
        async with self.__pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=self._timeout)

    async def fetchval(self, query, *args):
        async with self.__pool.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=self._timeout)

    async def get_user(self, user_id):
        """I'll implement this later"""
        raise NotImplementedError()

    async def get_all_users(self):
        """I'll implement this later"""
        raise NotImplementedError()

    async def close(self):
        """Closes the database"""
        if self.__pool:
            await self.__pool.close()
