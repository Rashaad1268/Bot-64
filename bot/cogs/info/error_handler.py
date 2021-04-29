import discord, logging, sys, random
import datetime as dt
from traceback import format_exc, format_exception

from discord.ext import commands
from discord.ext.commands import Context, command, errors

from bot.main import Bot
from bot.utils.helpful import build_error_embed
from bot.constants import RushGuild, Webhooks, NEGATIVE_REPLIES


log = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def handle_unhandled_exception(self, ctx: Context, error: Exception):
        exc = "".join(format_exception(error, error, error.__traceback__))
        print(exc)
        await ctx.send(
            "And Unhandled Exception Occured.\nPlease inform the Staff. about it"
        )
        webhook = discord.Webhook.from_url(
            Webhooks.dev_log, adapter=discord.AsyncWebhookAdapter(self.bot.http_session)
        )

        embed = discord.Embed(
            title="Unhandled Exception",
            colour=discord.Colour.red(),
            description=f"An unhandled exception occured for {self.bot.user.mention}\n**Exception:**```powershell\n{exc}```",
        )
        embed.add_field(
            name="Exception Class Name",
            value=f"```{error.__class__.__name__}```",
            inline=False,
        )
        embed.add_field(
            name="The command on which the error occured in",
            value=f"`{ctx.command.qualified_name}`",
            inline=False,
        )
        utc_time = dt.datetime.utcnow()
        embed.add_field(
            name="Time of occurrence (UTC)",
            value=utc_time.strftime("%d/%m/%Y %H:%M:%S"),
            inline=False,
        )
        embed.add_field(
            name="User who discovered this issue",
            value=f"{ctx.author.mention} ({str(ctx.author)})",
            inline=False,
        )
        embed.add_field(
            name="More info",
            value=f"[Message]({ctx.message.jump_url})",
            inline=False,
        )

        await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception):
        ignored_errors = (
            errors.CommandNotFound,
            errors.CheckFailure,
            errors.CheckAnyFailure,
            errors.MissingPermissions,
        )

        if hasattr(ctx.command, "on_error"):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        if ctx.cog:
            if ctx.cog.has_error_handler():
                return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored_errors):
            log.debug(
                f"{error.__class__.__name__} just occured. Ignoring it because it is in ignored_errors"
            )
            return

        elif isinstance(error, errors.MemberNotFound):
            em = build_error_embed(
                f"Unable to Find Member `{error.argument}`", title="MemberNotFound"
            )

        elif isinstance(error, errors.UserNotFound):
            em = build_error_embed(
                msg=f"Unable to Find User `{error.argument}`", title="UserNotFound"
            )

        elif isinstance(error, errors.ChannelNotFound):
            em = build_error_embed(
                f"Unable to Find Channel `{error.argument}`", title="ChannelNotFound"
            )

        elif isinstance(error, errors.MissingRequiredArgument):
            em = build_error_embed("Too few arguments supplied for this command")
            await ctx.send(embed=em)
            await ctx.send_help(ctx.command)
            return

        elif isinstance(error, errors.BadArgument):
            em = build_error_embed(error, title="BadArgument")

        elif isinstance(error, errors.CommandOnCooldown):
            em = build_error_embed(
                f"This command is on cool down for you, try again after {round(error.retry_after, 1)} seconds",
                title="Command On Cooldown",
            )

        elif isinstance(error, errors.CommandInvokeError):
            await self.handle_unhandled_exception(ctx, error)
            return

        else:
            # All unhandled errors will be handled here
            await self.handle_unhandled_exception(ctx, error)
            return

        log.debug(f"{error.__class__.__name__} just occured, handling it")
        await ctx.send(embed=em)


def setup(bot: Bot):
    bot.add_cog(ErrorHandler(bot))