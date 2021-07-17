import discord, asyncpg
from discord import Member, Embed
import typing as t

from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Context, Cog, command

from bot.main import Bot
from bot.utils.paginator import CustomPaginator
from bot.utils.helpful import build_error_embed, build_success_embed
from bot.utils.checks import is_staff, is_moderator, is_admin
from bot.constants import Colours, RushGuild


class LoggingInformation(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = self.bot.db
        self.members = self.bot.db.members

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        
        if message.guild.id != RushGuild.id:
            return

        if not message.author.bot:
            member_obj = await self.members.objects.get(message.author.id)
            if member_obj:
                await self.bot.db.messages(
                    id=message.id,
                    author=member_obj,
                    content=message.content or f"{message.author} sent a image",
                    channel_id=message.channel.id,
                    sent_at=message.created_at,
                ).save()

            elif not member_obj:
                try:
                    member = message.author
                    await self.members(
                        id=member.id,
                        name=member.name,
                        discriminator=member.discriminator,
                        in_guild=True,
                        joined_at=member.joined_at,
                    ).save()
                except asyncpg.exceptions.UniqueViolationError:
                    pass

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.guild:
            return
        
        if after.content != before.content:
            return

        if after.guild.id != RushGuild.id:
            return

        message_obj = await self.db.messages.objects.get(after.id)
        if message_obj:
            message_obj.content = after.content
            await message_obj.update()

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            try:
                await self.members(
                    id=member.id,
                    name=member.name,
                    discriminator=member.discriminator,
                    in_guild=True,
                    joined_at=member.joined_at,
                ).save()
            except asyncpg.exceptions.UniqueViolationError:
                member_obj = await self.members.objects.get(member.id)
                member_obj.in_guild = True
                await member_obj.update()

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not member.bot:
            member_in_db = await self.members.objects.get(member.id)
            if member_in_db:
                member_in_db.in_guild = False
                await member_in_db.update()

    @Cog.listener()
    async def on_user_update(self, before, after):
        member_in_db = await self.members.objects.get(after.id)
        if member_in_db:
            member_in_db.name = after.name
            member_in_db.discriminator = after.discriminator
            await member_in_db.update()

    @commands.group(
        name="database", aliases=["db", "databases"], invoke_without_command=True
    )
    async def database_command(self, ctx: Context):
        """The main group command for getting information from the database"""
        await ctx.send_help(ctx.command)

    @database_command.command(name="all-member-info", aliases=["ami", "members-info"])
    @is_admin()
    async def all_members_command(self, ctx: Context):
        """Sends information about all members in the database"""
        all_members = list()
        for db_member in await self.members.objects.all():
            messages_sent = await self.bot.db.messages.objects.filter(
                author=db_member.id
            )
            member_info = f"""**{db_member} (ID: {db_member.id})**\nMessages Sent: {messages_sent.count()} 
                               Joined At: {db_member.joined_at}\nTotal infractions: {db_member.total_infractions}\n"""
            all_members.append(member_info)
        embed = Embed(title="All members in the database", colour=Colours.light_blue)

        await CustomPaginator(all_members, embed, items_per_page=5).paginate(ctx)

    @database_command.command(name="member-info", aliases=["mi"])
    @is_moderator()
    async def member_info_command(self, ctx: Context, member: Member):
        """Sends information about a specified member from the database"""
        member_obj = await self.members.objects.get(member.id)
        if not member_obj:
            return await ctx.send(
                embed=build_error_embed(
                    "Looks like this member is not in the database."
                )
            )
        else:
            embed = discord.Embed(title=f"Information of {member.name}")
            messages_sent = await self.db.messages.objects.filter(author=member.id)
            description = str()
            description += f"Username: {str(member_obj)}\n"
            description += f"Id: {member_obj.id}\n"
            description += f"In Guild: {member_obj.in_guild}\n"
            description += f"Total Messages Sent: {messages_sent.count()}\n"
            description += (
                f"Total Infractions Received: {member_obj.total_infractions}\n"
            )
            description += (
                f"Joined at: {member_obj.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            )
            embed.description = description
            await ctx.send(embed=embed)

    @database_command.command(name="sync-members-db", aliases=["smd"])
    @commands.is_owner()
    async def sync_members_database(self, ctx: Context):
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await self.members(
                        id=member.id,
                        name=member.name,
                        discriminator=member.discriminator,
                        in_guild=True,
                        joined_at=member.joined_at,
                    ).save()
                except asyncpg.exceptions.UniqueViolationError:
                    pass
        await ctx.send(
            embed=build_success_embed(
                "Synced Members Database with current server members"
            )
        )

    @database_command.command(name="messages")
    @is_moderator()
    async def database_messages_command(
        self, ctx: Context, message_count: t.Optional[int] = None
    ):
        all_messages = await self.db.messages.objects.all()
        try:
            all_messages.raw[:message_count]
        except IndexError:
            await ctx.send(
                embed=build_error_embed(f"Index {message_count} doesn't exist")
            )
        to_send = list()
        for db_message in all_messages.raw[:message_count]:
            formatted = f"""Message Id: {db_message.id}\nAuthor: <@!{db_message.author}>
                            Content:\n{db_message.content}
                            Channel id: {db_message.channel_id}\nDate sent: {db_message.sent_at}\n"""
            to_send.append(formatted)
        await CustomPaginator(to_send).paginate(ctx)

    @database_command.command(
        name="messages-from", aliases=["msg-from", "msgs-from", "m-from"]
    )
    @is_moderator()
    async def database_messages_from_command(
        self, ctx: Context, from_member: Member, message_count: t.Optional[int] = None
    ):
        all_messages = await self.db.messages.objects.filter(author=from_member.id)
        try:
            all_messages.raw[:message_count]
        except IndexError:
            await ctx.send(
                embed=build_error_embed(f"Index {message_count} doesn't exist")
            )
        to_send = list()
        for db_message in all_messages.raw[:message_count]:
            formatted = f"""Message Id: {db_message.id}\nAuthor: <@!{db_message.author}>
                            Content:\n{db_message.content}
                            Channel id: {db_message.channel_id}\nDate sent: {db_message.sent_at}\n"""
            to_send.append(formatted)
        await CustomPaginator(to_send).paginate(ctx)


def setup(bot: Bot):
    bot.add_cog(LoggingInformation(bot))
