import asyncpg, datetime as dt, typing as t, asyncio, discord


class Tags:
    def __init__(self, bot):
        self.bot = bot

    async def __create_table(self):
        command = """
                  CREATE TABLE IF NOT EXISTS Tags(
                      Id SERIAL PRIMARY KEY,
                      Name VARCHAR(25),
                      Content TEXT,
                      AuthorId BIGINT,
                      DateCreated TIMESTAMP
                  );"""

        await self.bot.db.execute(command)

    async def create(self, tag_name: str, content: str, author: discord.Member):
        tag_name = tag_name.strip()
        content = content.strip()
        time = dt.datetime.utcnow()
        command = "INSERT INTO Tags (Name, Content, AuthorId, DateCreated) VALUES ($1, $2, $3, $4) RETURNING Id"

        try:
            return await self.bot.db.fetchval(command, tag_name, content, author.id, time)
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            return await self.bot.db.fetchval(command, tag_name, content, author.id, time)

    async def get_tag(self, tag_name: str):
        tag_name = tag_name.lower()
        tag_name = tag_name.strip()
        query = "SELECT * FROM Tags WHERE LOWER(Name) = $1"
        try:
            return await self.bot.db.fetchrow(query, tag_name)
        except asyncpg.UndefinedTableError:
            await self.__create_table()
            return None
        return None

    async def search(self, name: str):
        name = name.lower()
        name = name.strip()
        query = "SELECT Id, Name FROM Tags WHERE LOWER(Name) LIKE '%' || $1 || '%';"

        result = await self.bot.db.fetch(query, name)
        return result

    async def delete(self, tag_name: str):
        tag_name = tag_name.strip()
        tag_name = tag_name.lower()
        query = "DELETE FROM Tags WHERE LOWER(Name) = $1"
        await self.bot.db.execute(query, tag_name)
