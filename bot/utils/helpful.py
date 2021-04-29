import discord, asyncio, random, typing as t
from discord import Message, Embed
from discord.ext.commands import Context

from bot.constants import ERROR_REPLIES, POSITIVE_REPLIES, Colours


async def get_message(
    ctx: Context,
    content: t.Optional[str] = None,
    embed: t.Optional[Embed] = None,
    timeout: t.Optional[int] = 40,
):
    if embed and not content:
        sent = await ctx.send(embed=embed)

    elif content and not embed:
        sent = await ctx.send(content)

    elif content and embed:
        sent = await ctx.send(content, embed=embed)

    try:
        msg = await ctx.bot.wait_for(
            "message",
            timeout=timeout,
            check=lambda message: message.author == ctx.author
            and message.channel == ctx.channel,
        )
        if msg:
            return msg
    except asyncio.TimeoutError:
        return None


async def get_reply(
    ctx: Context,
    content: t.Optional[str] = None,
    embed: t.Optional[Embed] = None,
    timeout: t.Optional[int] = 40,
):
    msg = await get_message(ctx, content, embed, timeout)
    if msg:
        return msg.content
    return None


def build_success_embed(msg: str, **kwargs):
    return discord.Embed(
        title=kwargs.get("title", None) or random.choice(POSITIVE_REPLIES),
        description=msg,
        colour=kwargs.get("colour", None) or Colours.soft_green,
    )


def build_error_embed(msg: str, **kwargs):
    return discord.Embed(
        title=kwargs.get("title", None) or random.choice(ERROR_REPLIES),
        description=f":x: {msg}",
        colour=kwargs.get("colour", None) or Colours.red,
    )
