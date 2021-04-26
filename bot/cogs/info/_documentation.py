import discord

from discord.ext import commands
from discord.ext.commands import command, Context
from bs4 import BeautifulSoup

from bot.main import Bot
from bot.utils.helpful import build_error_embed


class Documentation(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def format_descr(self, descr):
        if len(descr) >= 1900:
            return f"{descr[:1900]}..."
        else:
            return f"{descr}"

    async def do_documentation(self, ctx: Context, query: str):
        lib = query.split(".")
        STDLIB_URL = "https://docs.python.org/3/library/"
        WHOLE_STDLIB_URL = STDLIB_URL + lib[0] + f".html#{query}"

        await ctx.trigger_typing()
        async with self.bot.http_session.get(WHOLE_STDLIB_URL) as resp:
            if resp.status == 200:
                soup = BeautifulSoup(await resp.text("utf-8"), "html.parser")

                try:
                    section = soup.find(id=query).parent

                except AttributeError:
                    section = soup.find(id="module-" + query)

                try:
                    doc_descr = section.dd.text
                except AttributeError:
                    try:
                        doc_descr = section.text
                    except AttributeError:
                        await ctx.send(
                            embed=build_error_embed(
                                "Could not find documentation for " + query
                            )
                        )
                        return

                embed = discord.Embed(
                    title=query, url=WHOLE_STDLIB_URL, colour=discord.Colour.blue()
                )
                embed.description = self.format_descr(doc_descr)

                await ctx.send(embed=embed)
                return

            else:
                # If the given query is not a module in the stdlib this checks if it is a built in function
                BUILTIN_FUNCTIONS_URL = (
                    "https://docs.python.org/3/library/functions.html"
                )
                WHOLE_FUNCTIONS_URL = BUILTIN_FUNCTIONS_URL + "#" + query

                async with self.bot.http_session.get(WHOLE_FUNCTIONS_URL) as resp:
                    if resp.status == 200:
                        soup = BeautifulSoup(await resp.text("utf-8"), "html.parser")

                        try:
                            section = soup.find(id=query).parent
                        except AttributeError:
                            await ctx.send(
                                embed=build_error_embed(
                                    "Could not find documentation for " + query
                                )
                            )
                            return

                        doc_descr = section.dd.text

                        title = soup.find(id=query).text
                        embed.description = self.format_descr(
                            WHOLE_FUNCTIONS_URL, title, doc_descr
                        )

                        await ctx.send(embed=embed)
                        return

                    else:
                        await ctx.send(
                            embed=build_error_embed(
                                "Could not find documentation for " + query
                            )
                        )
                        return

    @command(name="documentation", aliases=("d", "docs", "doc"))
    async def send_documentation(self, ctx: Context, query: str):
        await self.do_documentation(ctx, query)


def setup(bot: Bot):
    bot.add_cog(Documentation(bot))
