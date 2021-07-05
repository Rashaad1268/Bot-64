"""
Credit to https://github.com/python-discord/bot/blob/main/bot/exts/fun/off_topic_names.py
Thanks py-dis :)
"""

import discord, difflib, logging, random, datetime as dt
from discord import utils
from discord.ext import commands, tasks
from discord.ext.commands import command, group, Context

from bot.main import Bot
from bot.utils.checks import is_staff, is_admin, is_moderator
from bot.utils.helpful import build_success_embed, build_error_embed, get_reply
from bot.utils.converters import OffTopicName
from bot.utils.paginator import CustomPaginator
from bot.constants import RushGuild, Roles
from bot.database import off_topic_db

log = logging.getLogger(__name__)

CHANGE_PERIOD = 5  # <- minutes
COLOUR = discord.Color.blurple()


class OffTopicChannels(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.off_topic_names = self.bot.db.offtopicnames
        self.results_per_page = 5
        self.update_channel_names.start()

    @tasks.loop(hours=1)
    async def update_channel_names(self):
        """Updates the offtopic channel names to a random one from the pool"""
        log.debug("Changing ot channel names")
        all_names = await self.off_topic_names.objects.all()
        if not all_names.raw:
            log.info("Cancelling name change due to the table being empty")
            return
        channel_1_name = random.choice(all_names.raw)
        channel_2_name = random.choice(all_names.raw)

        channel_1 = self.bot.get_channel(RushGuild.Channels.off_topic_channels()[0])
        channel_2 = self.bot.get_channel(RushGuild.Channels.off_topic_channels()[1])

        await channel_1.edit(name=f"ot1-{channel_1_name}")
        await channel_2.edit(name=f"ot2-{channel_2_name}")

        log.debug("Changed ot channel names to " f"{channel_1_name} {channel_2_name}")

    @update_channel_names.before_loop
    async def before_channel_names_update(self):
        await self.bot.wait_until_guild_available()

    def cog_unload(self):
        self.update_channel_names.cancel()
        log.debug("Canceled off topic channel name update task")

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
            embed = build_success_embed(f"Added `{name}` to OffTopicNames DataBase")
            await ctx.send(embed=embed)

    @_off_topic_names.command(name="delete", aliases=["del", "d"])
    @is_admin()
    async def delete_off_topic_name(self, ctx, *, name: OffTopicName):
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
                    f"Channel name `{name}` is not in the OffTopicNames DataBase to delete"
                )
            )

    @_off_topic_names.command(name="search", aliases=["s"])
    @is_moderator()
    async def search_ot_names(self, ctx, *, query: OffTopicName):
        """Searches thorugh all of the off topic names"""
        search_results = await self.off_topic_names.search(query)
        if not search_results:
            await ctx.send(embed=build_error_embed(f"There are no search results for `{query}`"))

        embed = discord.Embed(
            title=f"Search results for {query}",
            colour=COLOUR,
        )
        await CustomPaginator(search_results, embed, items_per_page=4, prefix="```", suffix="```").paginate(ctx)

    @_off_topic_names.command(name="edit", aliases=("e", "update", "change"))
    async def change_ot_name(self, ctx: Context, *, name: OffTopicName):
        channel_name = await self.bot.db.fetchrow(
            "SELECT * FROM OffTopicNames WHERE Name = $1", name
        )
        if not channel_name:
            await ctx.send(
                embed=build_error_embed(
                    f"Channel name `{name}` is not in the OffTopicNames DataBase to edit"
                )
            )
            return

        new_name = await get_reply(ctx, "What is the new off topic channel name?")
        new_name = await OffTopicName().convert(ctx, new_name)
        admin_role = ctx.guild.get_role(Roles.admin)

        if channel_name["authorid"] == ctx.author.id or admin_role in ctx.author.roles:
            await self.bot.db.execute(
                "UPDATE OffTopicNames SET Name = $1 WHERE Name = $2", new_name, name
            )
            await ctx.send(
                embed=build_success_embed(f"Updated `{name}` to `{new_name}`")
            )

        else:
            await ctx.send(
                embed=build_error_embed("You do not have permissions to edit this name")
            )
            return

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
            names_entry = ""

            names_entry += "\n".join(next_names)
            pages.append(f"{names_entry}")

        pag = CustomPaginator(pages, embed, prefix="```", suffix="```")
        await pag.paginate(ctx)


def setup(bot: Bot):
    bot.add_cog(OffTopicChannels(bot))
