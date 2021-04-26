import discord, logging, datetime as dt, typing as t
from discord import Member
from discord.ext import commands, tasks
from discord import utils
from discord.ext.commands import command, Context

from bot.main import Bot
from bot.constants import Roles, RushGuild, Colours
from bot.utils.checks import is_staff
from bot.utils.helpful import build_error_embed, build_success_embed
from bot.utils.time import FutureTime

POLL_PERIOD = 5  # <- minutes


log = logging.getLogger(__name__)


class Mute(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.unmute_mutes.start()

    @tasks.loop(minutes=POLL_PERIOD)
    async def unmute_mutes(self):
        log.debug("Unmuting mutes")
        now = dt.datetime.utcnow()
        guild = self.bot.get_guild(RushGuild.id)
        muted_role = guild.get_role(Roles.muted)
        rows = await self.bot.db.mutes.everything()

        if rows:
            for row in rows:
                if row["expiry"]:
                    if now >= row["expiry"]:
                        target_member = guild.get_member(row["member_id"])

                        if target_member and muted_role in target_member.roles:
                            log.debug(f"Unmuted {str(target_member)}")
                            await target_member.remove_roles(muted_role)

                            await self.bot.db.mutes.remove_member(target_member.id)

    @unmute_mutes.before_loop
    async def before_check_current_mutes(self):
        await self.bot.wait_until_ready()

    async def inform_member(self, ctx: Context, member: Member, oppoite=False, **kwargs):
        msg = f"You are being {ctx.command.qualified_name} from {ctx.guild.name}"
        if not oppoite:
            msg += f"\nDuration: {kwargs.get('duration', 'Permanent')}\nReason: {kwargs.get('reason', None)}"

        title = kwargs.get('title', f'You are being {ctx.command.qualified_name}')
        embed = discord.Embed(title=title, description=msg, colour=Colours.soft_green if oppoite else Colours.soft_red)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

    async def unmute_user(self, ctx: Context, member: Member):
        muted_role = ctx.guild.get_role(Roles.muted)
        await member.remove_roles(muted_role)
        await self.bot.db.mutes.remove_member(member)
        await self.inform_member(ctx, member, True, title="You are being unmuted")
        await ctx.send(embed=build_success_embed(f"Unmuted {member.mention}"))
        log.debug(f"{str(ctx.author)} unmuted {str(member)}")

    async def perform_mute(self, ctx: Context, target: discord.Member, **kwargs):
        expiry = kwargs.get("expiry", None)
        reason = kwargs.get('reason', None)
        
        infraction = await self.bot.db.mutes.get_infraction(target)
        if ctx.command == self.mute_member and infraction:
            await ctx.send(embed=build_error_embed(
                        f"Member {target.mention} is already permanently muted\n"
                        f"See mute infraction `#{infraction['id']}`"
                    ))
            return


        await target.add_roles(discord.Object(id=Roles.muted), reason=reason)
        mute_id = await self.bot.db.mutes.add_member(target, expiry)
        success_embed = build_success_embed(
            f"Applied mute to {target.mention}\nReason: {reason}\n"
            f"Expiry: {expiry or 'Permanent'}"
        )
        success_embed.set_footer(text=f"Infraction Id: {mute_id}")
        await self.inform_member(ctx, target, expiry=expiry, reason=reason, title="You are being muted")
        await ctx.send(embed=success_embed)

    @command(name="mute")
    @is_staff()
    async def mute_member(self, ctx, target: Member, *, reason: t.Optional[str]=None):
        """Applies a permanent mute to a user"""
        await self.perform_mute(ctx, target, reason=reason)

    @command(name="temporary-mute", aliases=["tmute", "tempmute"])
    async def temporary_mute(
        self, ctx: Context, target: Member, expiry: FutureTime, *, reason: t.Optional[str] = None
    ):
        await self.perform_mute(ctx, target, expiry=expiry, reason=reason)

    @command(name="unmute")
    @is_staff()
    async def unmute_member(self, ctx: Context, member: Member):
        await self.unmute_user(ctx, member)


def setup(bot: Bot):
    bot.add_cog(Mute(bot))
