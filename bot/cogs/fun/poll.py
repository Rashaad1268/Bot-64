import discord
from discord.ext import commands
from discord.ext.commands import command

from bot.main import Bot
from bot.constants import Emojis
from bot.utils.helpful import get_message
from bot.utils.checks import is_staff, is_moderator
from bot.cogs._error_handeler import build_success_embed

class Poll(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.word_splitter = "?"

    @command(name='change-splitter', aliases=['change-split', 'ch-spl', 'ch-sp'])
    @is_moderator()
    async def change_splitter(self, ctx, new_splitter: str):
        """Changes the word splitter for polls"""
        self.word_splitter = new_splitter
        embed = build_success_embed(f"Successfully changed poll option word splitter to {new_splitter}")
        await ctx.send(embed=embed)

    @command()
    @is_staff()
    async def show_word_splitter(self, ctx):
        """Displays the word splitter for polls"""
        await ctx.send(f"The poll options word splitter is {self.word_splitter}")

    @command(name="poll", aliases=["start-poll"])
    @is_staff()
    async def start_poll(self, ctx, target_channel: discord.TextChannel=None, *, title="Poll"):
        """Starts a poll"""
        msg_to_send = "What are the poll options to vote on?"
        target_channel = target_channel or ctx.channel
        options = await get_message(ctx=ctx, content=msg_to_send)

        if not options:
            return

        options = options.split(self.word_splitter)

        poll_embed = discord.Embed(title=title, color=discord.Color.blue(), timestamp=ctx.message.created_at)
        poll_embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        poll_description = []

        if len(options) > 11:
            await ctx.send("You cannot have more than 10 poll options")
            return

        for key, option in enumerate(options):
            
            if option:
                poll_description.append(f"{Emojis.number_emojis[key + 1]} {option.strip()}")

        poll_embed.description = "\n\n".join(poll_description)

        poll_msg = await target_channel.send(embed=poll_embed)

        for key, option in enumerate(options):
            if not options[key]:
                return

            else:
                await poll_msg.add_reaction(Emojis.number_emojis[key + 1])


def setup(bot: Bot):
    bot.add_cog(Poll(bot))
