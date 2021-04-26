import discord
import typing as t

from discord.ext import commands
from discord.ext.commands import command, Context, group, has_permissions

from bot.main import Bot
from bot.constants import RushGuild


class Moderation(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name="send")
    async def dm_user(self, ctx, user: discord.User, *, msg: str):
        """DM's the messages to the given user"""
        await user.send(msg)
        await ctx.send(f"Sent: \n{msg}\nTo: {user.mention}")

    @command(name="echo")
    async def message_channel(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sends the message to the given channel"""
        await channel.send(message)

    @group(name="delete", aliases=["del"], invoke_without_command=True)
    @has_permissions(manage_messages=True)
    async def _delete(self, ctx):
        """The main delete command"""
        await ctx.send_help(ctx.command)

    @_delete.command(name="search", aliases=["s"])
    @has_permissions(manage_messages=True)
    async def delete_messages_search(self, ctx, limit: int, *, text: str):
        """Deletes the given number of messages which has the given text"""
        await ctx.message.delete()
        msgs_to_delete = []
        async for msg in ctx.channel.history(limit=limit):
            if msg.content.lower() in text.lower():
                msgs_to_delete.append(msg)

        for i in range(0, len(msgs_to_delete), 100):
            await ctx.channel.delete_messages(msgs_to_delete[i : i + 100])

    @_delete.command(name="messages", aliases=("m", "msg", "msgs"))
    @has_permissions(manage_messages=True)
    async def delete_channel_messages(
        self, ctx, limit: int, channel: t.Optional[discord.TextChannel] = None
    ):
        """Deletes the given amount of messages in the specified channel or the current one"""
        channel = channel or ctx.channel
        await channel.purge(limit=limit + 1)

    @_delete.command(name="all", aliases=("a",))
    @has_permissions(administrator=True)
    async def delete_messages_in_all_channels(
        self, ctx, limit: int, author: t.Optional[discord.Member]=None
    ):
        """Deletes the given number of messages in all non staff channels optionally sent by a specific user"""
        for channel in ctx.guild.text_channels:
            if channel.id not in RushGuild.Channels.staff_channels():
                if author:
                    await channel.purge(
                        limit=limit, check=lambda m: m.author.id == author.id
                    )
                else:
                    await channel.purge(limit=limit)


    @commands.Cog.listener()
    async def on_message(self, message):
        guild = self.bot.get_guild(RushGuild.id)

        if message.author.id == self.bot.user.id:
            return

        if str(message.channel.type) == "private":
            special_channel = discord.utils.get(guild.channels, name="admin-stuff")
            if message.attachments:
                for attachment in message.attachments:
                    await special_channel.send(
                        f"{message.author.mention} sent attachment(s)"
                    )
                    await special_channel.send(attachment.url)
            else:
                await special_channel.send(
                    f"""{message.author.mention} sent this in a DM:\n{message.content}"""
                )
            return


def setup(bot: Bot):
    bot.add_cog(Moderation(bot))
