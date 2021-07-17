import discord, logging, datetime as dt, typing as t, contextlib
from discord import Member
from discord.ext import commands, tasks
from discord import utils
from discord.ext.commands import command, Context, guild_only

from bot.main import Bot
from bot.constants import Roles, RushGuild, Colours
from bot.utils.checks import is_staff
from bot.utils.helpful import build_error_embed, build_success_embed
from bot.utils.time import FutureTime, human_timedelta

POLL_PERIOD = 25  # <- minutes


log = logging.getLogger(__name__)


class Mute(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.mutes = self.bot.db.mutes
        self.members = self.bot.db.members
        self.unmute_mutes.start()

    @tasks.loop(minutes=POLL_PERIOD)
    async def unmute_mutes(self):
        log.debug("Unmuting muted members")
        now = dt.datetime.utcnow()
        guild = self.bot.get_guild(RushGuild.id)
        muted_role = guild.get_role(Roles.muted)
        all_mutes = await self.mutes.objects.all()

        if all_mutes:
            for mute in all_mutes:
                if mute.expiry:
                    if now >= mute.expiry:
                        to_unmute = await self.members.objects.get(mute.member)
                        target_member = guild.get_member(to_unmute.id)

                        if target_member and muted_role in target_member.roles:
                            log.debug(f"Unmuted {str(target_member)}")
                            await target_member.remove_roles(muted_role)
                            await mute.delete()

                        elif target_member and muted_role not in target_member.roles:
                            await mute.delete()

    @unmute_mutes.before_loop
    async def before_check_current_mutes(self):
        await self.bot.wait_until_guild_available()

    async def inform_member(
        self, ctx: Context, member: Member, oppoite=False, **kwargs
    ):
        infraction_type = kwargs.get("infraction_type", ctx.command.qualified_name)
        expiry = kwargs.get("expiry", None)
        reason = kwargs.get("Reason", None)
        msg = f"You are being {infraction_type} from {ctx.guild.name}"
        if not oppoite:
            msg += f"\nExpiry: {expiry.strftime('%d/%m/%Y %H:%M:%S') if expiry else 'Permanent'}{f' ({human_timedelta(expiry)})' if expiry else ''}\nReason: {reason}"

        title = f"You are being {infraction_type}"
        embed = discord.Embed(
            title=title,
            description=msg,
            colour=Colours.soft_green if oppoite else Colours.soft_red,
        )
        with contextlib.suppress(discord.Forbidden):
            await member.send(embed=embed)

    async def unmute_user(self, ctx: Context, member: Member, **kwargs):
        send_message = kwargs.get("send_message", True)
        send_dm = kwargs.get("send_dm", True)
        muted_role = ctx.guild.get_role(Roles.muted)
        await member.remove_roles(muted_role)
        infraction = await self.mutes.objects.get(member=member.id)
        await infraction.delete()

        if send_dm:
            await self.inform_member(ctx, member, True, infraction_type="unmuted")

        if send_message:
            await ctx.send(embed=build_success_embed(f"Unmuted {member.mention}"))

        log.debug(f"{str(ctx.author)} unmuted {str(member)}")

    async def perform_mute(self, ctx: Context, target: discord.Member, **kwargs):
        expiry = kwargs.get("expiry", None)
        reason = kwargs.get("reason", None)
        is_permanent = True if expiry else False
        send_dm = kwargs.get("send_dm", True)
        infraction_type = kwargs.get(
            "infraction_type", "temporary mute" if expiry else "mute"
        )

        target_in_db = await self.members.objects.get(target.id)
        infraction = await self.mutes.objects.get(member=target_in_db.id)
        if is_permanent and infraction is not None:
            await ctx.send(
                embed=build_error_embed(
                    f"Member {target.mention} is already permanently muted\n"
                    f"See mute infraction `#{infraction.id}`"
                )
            )
            return

        await target.add_roles(discord.Object(id=Roles.muted), reason=reason)
        target_in_db.total_infractions += 1
        await target_in_db.update()
        dm_inf_type = "temporarily muted" if is_permanent else "muted"
        mute = await self.mutes.objects.create(
            member=target_in_db.id,
            expiry=expiry,
            reason=reason,
            given_at=dt.datetime.utcnow(),
        )
        formatted_expiry = (
            expiry.strftime("%d/%m/%Y %H:%M:%S") if expiry else "Permanent"
        )
        success_embed = build_success_embed(
            f"Applied {infraction_type} to {target.mention}\nReason: {reason}\n"
            f"Expiry: {formatted_expiry}{f' ({human_timedelta(expiry)})' if expiry else ''}"
        )
        success_embed.set_footer(text=f"Infraction Id: {mute.id}")

        if send_dm:
            await self.inform_member(
                ctx, target, expiry=expiry, reason=reason, infraction_type=dm_inf_type
            )
        await ctx.send(embed=success_embed)

        if expiry:
            await discord.utils.sleep_until(expiry)
            await self.unmute_user(ctx, target, send_message=False, send_dm=send_dm)

    @command(name="mute")
    @guild_only()
    @is_staff()
    async def mute_member(self, ctx, target: Member, *, reason: t.Optional[str] = None):
        """Applies a permanent mute to a user"""
        await self.perform_mute(ctx, target, reason=reason)

    @command(name="tempmute", aliases=["tmute", "temporary-mute"])
    @guild_only()
    @is_staff()
    async def temporary_mute(
        self,
        ctx: Context,
        target: Member,
        expiry: FutureTime,
        *,
        reason: t.Optional[str] = None,
    ):
        await self.perform_mute(ctx, target, expiry=expiry.dt, reason=reason)

    @command(name="unmute", aliases=["umute"])
    @guild_only()
    @is_staff()
    async def unmute_command(self, ctx: Context, member: Member):
        await self.unmute_user(ctx, member)

    @command(name="shadow-unmute", aliases=["shadow-umute"])
    @guild_only()
    @is_staff()
    async def shadow_unmute_command(self, ctx: Context, member: Member):
        await self.unmute_user(ctx, member, send_dm=False)

    @command(name="shadow-mute")
    @guild_only()
    @is_staff()
    async def shadow_mute(
        self, ctx: Context, target: Member, *, reason: t.Optional[str] = None
    ):
        await self.perform_mute(ctx, target, reason=reason, send_dm=False)

    @command(name="shadow-tempmute", aliases=["shadow-tmute"])
    @guild_only()
    @is_staff()
    async def shadow_tempmute(
        self,
        ctx: Context,
        target: Member,
        expiry: FutureTime,
        *,
        reason: t.Optional[str] = None,
    ):
        await self.perform_mute(
            ctx, target, expiry=expiry.dt, reason=reason, send_dm=False
        )


def setup(bot: Bot):
    bot.add_cog(Mute(bot))
