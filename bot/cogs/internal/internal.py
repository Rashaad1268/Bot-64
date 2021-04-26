import discord
import math, io, re, contextlib, textwrap, arrow
from traceback import format_exception
from dateutil.relativedelta import relativedelta

from discord.ext import commands
from discord.ext.commands import command

from bot.main import Bot
from bot.utils.checks import is_staff
from bot.utils.paginator import CustomPaginator
from bot.constants import Colours


class Internal(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def clean_code(self, code):
        """
        Credit to https://github.com/python-discord/bot/blob/main/bot/exts/utils/internal.py#L221-L229 for the regex to escape discord markdown
        And to https://github.com/MenuDocs/Discord.PY-Tutorials/blob/Episode-27/bot.py#L138-L175 for the eval command
        """
        code = code.strip("`")
        if re.match("py(thon)?\n", code):
            code = "\n".join(code.split("\n")[1:])

        if (
            not re.search(  # Check if it's an expression
                r"^(return|import|for|while|def|class|" r"from|exit|[a-zA-Z0-9]+\s*=)",
                code,
                re.M,
            )
            and len(code.split("\n")) == 1
        ):
            code = "_ = " + code

        return code

    @command(name="eval", aliases=["e"])
    @commands.is_owner()
    async def internal_eval(self, ctx, *, code):
        """Executes the given code."""
        code = self.clean_code(code)

        local_variables = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "self": self,
            "math": math,  # Yes, I also use this to do my math homework
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}",
                    local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"
                embed = discord.Embed(description=result, colour=Colours.blue)

        except Exception as e:
            result = "".join(format_exception(e, e, e.__traceback__))
            embed = discord.Embed(title="Eval output", colour=discord.Colour.red())

        await CustomPaginator(
            pages=[result[i : i + 2000] for i in range(0, len(result), 2000)],
            initial_embed=embed,
            timeout=100,
            prefix="```powershell\n",
            suffix="```",
        ).paginate(ctx)

    @command()
    @is_staff()
    async def uptime(self, ctx):
        """Shows how long the bot has been running"""
        "Inspired by https://github.com/python-discord/sir-lancebot/blob/main/bot/exts/evergreen/uptime.py#L18-L28"
        uptime_string = self.bot.utc_start_time.humanize()
        await ctx.send(f"I started up {uptime_string}.")


def setup(bot: Bot):
    bot.add_cog(Internal(bot))
