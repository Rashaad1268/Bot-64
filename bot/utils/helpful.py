import discord, asyncio, random
from discord import Message, Embed
from discord.ext.commands import Context

from bot.constants import ERROR_REPLIES, POSITIVE_REPLIES, Colours


async def get_message(
    ctx: Context, content: str = None, embed: Embed = None, timeout: int = 40
):
    if embed:
        sent = await ctx.send(embed=embed)

    if content:
        sent = await ctx.send(content)

    try:
        msg = await ctx.bot.wait_for(
            "message",
            timeout=timeout,
            check=lambda message: message.author == ctx.author
            and message.channel == ctx.channel,
        )
        if msg:
            return msg.content
    except asyncio.TimeoutError:
        return None


def build_success_embed(msg: str, **kwargs):
    return discord.Embed(
        title=kwargs.get('title', None) or random.choice(POSITIVE_REPLIES),
        description=msg,
        colour=kwargs.get('colour', None) or Colours.soft_green
    )


def build_error_embed(msg: str, **kwargs):
    return discord.Embed(
        title=kwargs.get('title', None) or random.choice(ERROR_REPLIES),
        description=f":x: {msg}",
        colour=kwargs.get('colour', None) or Colours.red,
    )
