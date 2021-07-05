import discord
from discord import Member, Embed
import typing as t

from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Context, Cog, command

from bot.main import Bot
from bot.utils.paginator import CustomPaginator
from bot.utils.helpful import build_error_embed
from bot.utils.checks import is_staff, is_moderator, is_admin
from bot.constants import Colours


class LoggingInformation(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.members = self.bot.db.members

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot and message.guild:
            member_obj = await self.members.objects.get(message.author.id)
            if member_obj:
                member_obj.message_count += 1
                await member_obj.update()

                await self.bot.db.messages(
                    id=message.id,
                    author=member_obj,
                    content=message.content or f"{message.author} sent a image",
                    sent_at=message.created_at,
                ).save()

            elif not member_obj:
                member = message.author
                await self.members(
                    id=member.id,
                    name=member.name,
                    discriminator=member.discriminator,
                    in_guild=True,
                    joined_at=member.joined_at,
                ).save()

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            await self.members(
                id=member.id,
                name=member.name,
                discriminator=member.discriminator,
                in_guild=True,
                joined_at=member.joined_at,
            ).save()

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

    @commands.group(name="database", aliases=["db", "databases"], invoke_without_command=True)
    async def database_command(self, ctx: Context):
        """The main group command for getting information from the database"""
        await ctx.send_help(ctx.command)

    @database_command.command(name="all-member-info", aliases=["ami", "members-info"])
    @is_admin()
    async def all_members_command(self, ctx: Context):
        """Sends information about all members in the database"""
        all_members = list()
        for db_member in await self.members.objects.all():
            member_info = f"""{db_member} ID: {db_member.id} Messages Sent: {db_member.message_count} 
                               Joined At: {db_member.joined_at} Total infractions: {db_member.total_infractions}\n"""
            all_members.append(member_info)
        embed = Embed(title="All members in the database", colour=Colours.blue)

        await CustomPaginator(all_members, embed).paginate(ctx)

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
            description = str()
            description += f"Username: {str(member_obj)}\n"
            description += f"Id: {member_obj.id}\n"
            description += f"In Guild: {member_obj.in_guild}\n"
            description += f"Total Messages Sent: {member_obj.message_count}\n"
            description += f"Total Infractions Received: {member_obj.total_infractions}\n"
            description += (
                f"Joined at: {member_obj.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            )
            embed.description = description
            await ctx.send(embed=embed)


def setup(bot: Bot):
    bot.add_cog(LoggingInformation(bot))
