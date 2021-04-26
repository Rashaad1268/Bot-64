import discord, os, arrow, asyncio, aiohttp, logging

from discord.ext import commands
import nest_asyncio

from .constants import BotConfig, Postgress
from bot.database.database import DataBase

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        activity = kwargs.get(
            "activity", discord.Game(name=f"Commands {BotConfig.prefix}help")
        )
        super().__init__(**kwargs, activity=activity)

        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self.db = self.loop.run_until_complete(
            DataBase.create(Postgress.uri, self, self.loop)
        )

    @property
    def rush(self):
        return self.get_user(self.owner_id)

    @classmethod
    def defaults(cls):
        allowed_mentions = discord.AllowedMentions(
            everyone=False, users=True, roles=True, replied_user=True
        )
        return cls(
            command_prefix=commands.when_mentioned_or(BotConfig.prefix),
            intents=BotConfig.intents,
            owner_id=BotConfig.owner_id,
            allowed_mentions=allowed_mentions,
        )

    async def close(self):
        """Closes the bot"""
        log.info("Getting ready to close the bot")

        await super().close()
        log.info("Closed the bot using super().close()")

        if self.http_session:
            log.info("Closed aiohttp ClientSession")
            await self.http_session.close()

        if self.db:
            log.info("Closed Data base")
            await self.db.close()

        if self.loop:
            log.info("Cloed loop")
            nest_asyncio.apply(self.loop)

    async def on_ready(self):
        print(f"We have logged in as {str(self.user)} ID: {self.user.id}")

    async def on_connect(self):
        log.debug("Connected to the Discord API")
        self.utc_start_time = arrow.utcnow()

    def load_extension(self, name):
        super().load_extension(name)
        log.info(f"Loaded external {name}")
