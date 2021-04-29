import discord, datetime as dt, asyncpg, random
from discord import Member


class OffTopicNames:
    def __init__(self, bot):
        self.bot = bot

    async def __create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS OffTopicNames(
            Id SERIAL PRIMARY KEY,
            Name VARCHAR(50) UNIQUE,
            AuthorId BIGINT,
            DateAdded TIMESTAMP
        );"""

        await self.bot.db.execute(query)

    async def add_name(self, name, author: Member):
        time = dt.datetime.utcnow()
        query = (
            "INSERT INTO OffTopicNames (Name, AuthorId, DateAdded) VALUES($1, $2, $3)"
        )

        try:
            await self.bot.db.execute(query, name, author.id, time)
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            await self.bot.db.execute(query, name, author.id, time)

    async def delete_name(self, name):
        query = "DELETE FROM OffTopicNames WHERE Name = $1"

        try:
            await self.bot.db.execute(query, name)
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            await self.bot.db.execute(query, name)

    async def search(self, name: str):
        query = (
            "SELECT Name FROM OffTopicNames WHERE LOWER(Name) LIKE '%' || $1 || '%';"
        )
        try:
            result = await self.bot.db.fetch(query, name.lower())
            return [name["name"] for name in result]

        except asyncpg.UndefinedTableError:
            await self.__create_table()
            result = await self.bot.db.fetch(query, name.lower())
            return [name for name in result]

    async def random_name(self):
        query = "SELECT Name FROM OffTopicNames;"

        try:
            names = await self.bot.db.fetch(query)
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            return

        try:
            random_name = random.choice(names)
            return random_name["name"]
        except IndexError:
            return None

    async def all_names(self):
        query = "SELECT Name FROM OffTopicNames;"

        try:
            all_names = await self.bot.db.fetch(query)
            return [name["name"] for name in all_names]
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            return None  # Just created the table
