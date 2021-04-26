import discord, traceback, random, logging, sys, traceback
import datetime as dt
from discord.ext.commands import errors
from discord.ext import commands

from bot.constants import ERROR_REPLIES, NEGATIVE_REPLIES, POSITIVE_REPLIES


log = logging.getLogger(__name__)

def build_error_embed(error_description: str):
    error_embed = discord.Embed(title=random.choice(
        ERROR_REPLIES), description=f":x: {error_description}", color=discord.Color.red())
    return error_embed

def build_success_embed(success_message: str):
    success_embed = discord.Embed(title=random.choice(
        POSITIVE_REPLIES), description=success_message, color=discord.Color.green())
    return success_embed


def build_log_embed(ctx: commands.Context, moderator: discord.Member, log_message: str):
    log_embed = discord.Embed(color=discord.Color.light_gray(
    ), title="Moderation Log", description=log_message, timestamp=ctx.message.created_at)
    log_embed.set_footer(text=str(moderator))
    return log_embed


def format_error(e: Exception):
    return "".join(traceback.format_exception(e, e, e.__traceback__))


async def handle_errors(ctx: commands.Context, error):
    ignored_errors = (errors.NotOwner, errors.CommandNotFound, errors.MissingPermissions, errors.MissingAnyRole, errors.MissingAnyRole)
    if isinstance(error, ignored_errors):
        return

    elif isinstance(error, errors.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown for you.\nTry again after {round(error.retry_after, 1)} seconds.")

    elif isinstance(error, errors.MemberNotFound):
        await ctx.send(f"Unable to Find Member `{error.argument}`")
        log.debug(f"{error}\n")
        return

    elif isinstance(error, errors.MissingRequiredArgument):
        await ctx.send(f"You have not given the `{error.param.name}` argument")
        log.debug(f"{error}\n")
        return

    elif isinstance(error, errors.ChannelNotFound):
        await ctx.send(f"Unable to find Channel `{error.argument}`")
        log.debug(f"{error}\n")
        return

    elif isinstance(error, errors.CommandInvokeError):
        formatted_error = format_error(error)
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        print(formatted_error)
        await ctx.send(f"An unhandeled exception occurred while processing command {ctx.command.qualified_name}\n```powershell\n{formatted_error}```")


    elif isinstance(error, errors.BadArgument):
        await ctx.send(f"{error.param.name} is a bad argument.")
        log.debug(f"{error}\n")

    else:
        # All unhandled Errors will print their original traceback
        print('Ignoring exception in command {}:'.format(
            ctx.command), file=sys.stderr)

        formatted_error = format_error(error)
        print(formatted_error)
        

        await ctx.send(f"An unhandeled exception occurred here are some details\n{formatted_error}")
