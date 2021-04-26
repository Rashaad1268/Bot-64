import discord, logging
import typing as t
from discord.ext import commands
from discord.ext.commands import check, has_any_role, Context, CheckFailure

from bot.constants import MODERATION_ROLES, STAFF_ROLES, Roles, RushGuild, DeleteMessage


log = logging.getLogger(__name__)


def has_any_role_check(ctx: Context, *roles: t.Union[t.Tuple[int], t.List[int]]):
    for role in ctx.author.roles:
        if role.id in STAFF_ROLES:
            return True


def is_admin():
    return has_any_role(*(Roles.owner, Roles.admin))

def is_moderator():
    return has_any_role(*MODERATION_ROLES)


def is_staff():
    return has_any_role(*STAFF_ROLES)


def in_valid_channels():
    async def predicate(ctx: Context):
        if ctx.author.id == RushGuild.owner_id:
            log.debug(f"{ctx.author} is the Rush2618#7876 (aka my creator) so he passes the in_valid_channels check")
            return True

        if has_any_role_check(ctx, STAFF_ROLES[:-1]):
            if ctx.channel.id in RushGuild.Channels.valid_channels():
                log.debug(f"{ctx.author} is a staff member and also is using this command in a valid_channel check passed")
                return True
            else:
                try:
                    log.debug(f"{ctx.author} is a staff member but isn't using this command in a valid_channel check failed")
                    await ctx.send(
                        f"Please use <#{RushGuild.Channels.staff_bot_commands}> for this command",
                        delete_after=DeleteMessage.bot_msg_delete_delay,
                    )
                    await ctx.message.delete(delay=DeleteMessage.user_msg_delete_delay)
                except discord.NotFound:
                    log.info(
                        f"discord.NotFound error raised while trying to delete messages which failed the in_valid_channel check, ignoring the error"
                    )
                    pass
                return None

        if ctx.channel.id in RushGuild.Channels.valid_channels():
            log.debug(
                f"{ctx.author} is not staff but is using the command in a valid channel, check passed"
            )
            return True
        else:
            try:
                log.debug(f"{ctx.author} is not staff and also not using the command in a valid channel, check failed")
                await ctx.send(
                    f"Please use <#{RushGuild.Channels.public_bot_commands}> for this command",
                    delete_after=DeleteMessage.user_msg_delete_delay)
                await ctx.message.delete(delay=DeleteMessage.user_msg_delete_delay)
            except discord.NotFound:
                log.info(f"discord.NotFound error raised while trying to delete messages which failed the in_valid_channel check, ignoring the error")
                pass
            return None

    return check(predicate)