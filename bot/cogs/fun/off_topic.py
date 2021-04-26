"""
Credit to https://github.com/python-discord/bot/blob/main/bot/exts/fun/off_topic_names.py
Thanks py-dis :)
"""

import discord, difflib, logging, datetime as dt
from discord import utils
from discord.ext import commands, tasks
from discord.ext.commands import command, group

from bot.main import Bot
from bot.utils.checks import is_staff, is_admin, is_moderator
from bot.utils.helpful import build_success_embed, build_error_embed
from bot.utils.converters import OffTopicName
from bot.utils.paginator import CustomPaginator
from bot.constants import RushGuild
from bot.database import off_topic_db

log = logging.getLogger(__name__)

CHANGE_PERIOD = 5  # <- minutes
COLOUR = discord.Color.blurple()


class OffTopicChannels(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.off_topic_names = off_topic_db.OffTopicNames(self.bot)
        self.results_per_page = 5
        self.update_channel_names.start()

    @tasks.loop(minutes=5)
    async def update_channel_names(self):
        """Updates the offtopic channel names to a random one from the pool"""
        log.debug("Changing ot channel names")
        channel_1_name = await self.off_topic_names.random_name()
        channel_2_name = await self.off_topic_names.random_name()

        channel_1 = self.bot.get_channel(
            RushGuild.Channels.off_topic_channels()[0]
        )
        channel_2 = self.bot.get_channel(
            RushGuild.Channels.off_topic_channels()[1]
        )

        await channel_1.edit(name=f"ot1-{channel_1_name}")
        await channel_2.edit(name=f"ot2-{channel_2_name}")

        log.debug("Changed ot channel names to " f"{channel_1_name} {channel_2_name}")

    @update_channel_names.before_loop
    async def before_channel_names_update(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.update_channel_names.cancel()
        log.debug("Canceled off topic channel update task")

    @group(name="off-topic-names", aliases=["otn"], invoke_without_command=True)
    async def _off_topic_names(self, ctx):
        """Off topic names group"""
        await ctx.send_help(ctx.command)

    @_off_topic_names.command(name="add", aliases=["a"])
    async def add_off_topic_channel_name(self, ctx, *, name: OffTopicName):
        """Adds a channel name to the pool"""
        existing_names = await self.off_topic_names.all_names()

        if close_match := difflib.get_close_matches(
            name, existing_names, n=1, cutoff=0.8
        ):
            match = close_match[0]
            log.info(
                f"{ctx.author} tried to add {name} off topic channel name to the db but it was too similar to {match}"
            )

            err_em = build_error_embed(
                f"Channel name `{name}` is too similar to `{match}`, thus it was not added"
            )
            await ctx.send(embed=err_em)

        else:
            await self.off_topic_names.add_name(name, ctx.author)
            embed = build_success_embed(f"Added `{name}` to off topic channel names")
            await ctx.send(embed=embed)

    @_off_topic_names.command(name="delete", aliases=["del", "d"])
    @is_admin()
    async def delete_off_topic_name(self, ctx, name: OffTopicName):
        """Deletes a given off topic name"""
        if name in await self.off_topic_names.all_names():
            await self.off_topic_names.delete_name(name)
            await ctx.send(
                embed=build_success_embed(f"Deleted `{name}` from OffTopicNames pool")
            )
            return
        else:
            await ctx.send(
                embed=build_error_embed(
                    f"Channel name `{name}` is not in the Channel Names pool to delete"
                )
            )

    @_off_topic_names.command(name="search", aliases=["s"])
    @is_moderator()
    async def search_ot_names(self, ctx, query: OffTopicName):
        """Searches thorugh all of the off topic names"""
        search_results = await self.off_topic_names.search(query)

        embed = discord.Embed(
            title="Search results",
            description="\n".join(search_results)
            or f"There are no search results for `{query}`",
            colour=COLOUR,
        )
        await ctx.send(embed=embed)

    @_off_topic_names.command(name="list", aliases=["l"])
    @is_moderator()
    async def list_ot_names(self, ctx):
        """Lists all of the off topic names"""
        all_names = await self.off_topic_names.all_names()
        embed = discord.Embed(
            title="Here are all of the off-topic names", colour=COLOUR
        )
        pages = []

        for i in range(0, len(all_names), self.results_per_page):
            next_names = all_names[i : i + self.results_per_page]
            names_entry = "```\n"

            names_entry += "\n".join(next_names)
            names_entry += "```"
            pages.append(f"{names_entry}")

        pag = CustomPaginator(pages, embed)
        await pag.paginate(ctx)


def setup(bot: Bot):
    bot.add_cog(OffTopicChannels(bot))
