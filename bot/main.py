import discord, os, arrow, asyncio, aiohttp, logging

from discord.ext import commands
import nest_asyncio

from .constants import (BotConfig, RushGuild, Roles, Webhooks)
from bot.models import DataBase

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        kwargs.setdefault("activity", discord.Game(name=f"Commands {BotConfig.prefix}help"))
        super().__init__(**kwargs)

        self.db = DataBase()
        self.http_session = aiohttp.ClientSession(loop=self.loop)
        self._guild_available  = asyncio.Event()

    @property
    def rush(self):
        return self.get_user(self.owner_id)

    @classmethod
    def defaults(cls):
        allowed_mentions = discord.AllowedMentions(
            everyone=False, users=True, roles=False, replied_user=True
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
        log.info("Closed the bot")

        if self.http_session:
            await self.http_session.close()
            log.info("Closed aiohttp ClientSession")

        if self.db:
            await self.db.close()
            log.info("Closed Data base pool")

        if self.loop:
            log.info("Cloed event loop")
            nest_asyncio.apply(self.loop)

    def load_extension(self, name):
        super().load_extension(name)
        log.info(f"Loaded external {name}")

    async def on_ready(self):
        print(f"We have logged in as {str(self.user)} ID: {self.user.id}")
        self.utc_start_time = arrow.utcnow()

    async def on_connect(self):
        log.debug("Connected to the Discord API")
    
    async def on_guild_available(self, guild: discord.Guild):
        """
        Set the internal guild available event when constants.Guild.id becomes available.
        If the cache appears to still be empty (no members, no channels, or no roles), the event
        will not be set.
        """
        if guild.id != RushGuild.id:
            return

        if not guild.roles or not guild.members or not guild.channels:
            msg = "Guild available event was dispatched but the cache appears to still be empty!"
            log.warning(msg)

            try:
                webhook = await self.fetch_webhook(Webhooks.dev_log)
            except discord.HTTPException as e:
                log.error(f"Failed to fetch webhook to send empty cache warning: status {e.status}")
            else:
                await webhook.send(f"<@&{Roles.admin}> {msg}")

            return

        self._guild_available.set()

    async def on_guild_unavailable(self, guild: discord.Guild):
        """Clear the internal guild available event when constants.RushGuild.id becomes unavailable."""
        if guild.id != RushGuild.id:
            return

        self._guild_available.clear()

    async def wait_until_guild_available(self) -> None:
        """
        Thanks py-dis :)
        Wait until the constants.RushGuild.id guild is available (and the cache is ready).
        The on_ready event is inadequate because it only waits 2 seconds for a GUILD_CREATE
        gateway event before giving up and thus not populating the cache for unavailable guilds.
        """
        await self._guild_available.wait()
