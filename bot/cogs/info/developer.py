import io
import os
import re
import zlib

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import command, Context

from bot.constants import BotConfig


DOC = {
        "antispam": "https://dpy-anti-spam.readthedocs.io/en/latest",
        "discord.py": "https://discordpy.readthedocs.io/en/latest",
        "py": "https://docs.python.org/3",
        "asyncpg": "https://magicstack.github.io/asyncpg/current",
        "django": "https://docs.djangoproject.com/en/3.2/"
}



# Sphinx reader pbject because d.py docs
# are written in sphinx.
class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


class Docs(commands.Cog, name="Documentation"):
    def __init__(self, bot):
        self.bot = bot
        self.page_types = DOC

    def finder(self, text, collection, *, key=None, lazy=True):
        suggestions = []
        text = str(text)
        pat = ".*?".join(map(re.escape, text))
        regex = re.compile(pat, flags=re.IGNORECASE)
        for item in collection:
            to_search = key(item) if key else item
            r = regex.search(to_search)
            if r:
                suggestions.append((len(r.group()), r.start(), item))

        def sort_key(tup):
            if key:
                return tup[0], tup[1], key(tup[2])
            return tup

        if lazy:
            return (z for _, _, z in sorted(suggestions, key=sort_key))
        else:
            return [z for _, _, z in sorted(suggestions, key=sort_key)]

    def parse_object_inv(self, stream, url):
        # key: URL
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        stream.readline().rstrip()[11:]
        stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            result[f"{prefix}{key}"] = os.path.join(url, location)

        return result

    async def build_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            try:
                async with self.bot.http_session.get(page + "/objects.inv") as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            "Cannot build rtfm lookup table, try again later."
                        )

                    stream = SphinxObjectFileReader(await resp.read())
                    cache[key] = self.parse_object_inv(stream, page)
            except RuntimeError:
                async with self.bot.http_session.get(page + "/_objects") as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            "Cannot build rtfm lookup table, try again later."
                        )

                    stream = SphinxObjectFileReader(await resp.read())
                    cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def send_doc(self, ctx, key, obj):
        page_types = self.page_types
        key = key.lower()

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, "_rtfm_cache"):
            await ctx.trigger_typing()
            await self.build_lookup_table(page_types)

        cache = list(self._rtfm_cache[key].items())

        self.matches = self.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = discord.Embed(description=f"**Query:** `{obj}`\n\n", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
        if len(self.matches) == 0:
            return await ctx.send("Could not find anything. Sorry.")

        e.description += "\n".join(f"[`{key}`]({url})" for key, url in self.matches)
        e.set_footer(text=f"Requested by: {ctx.author.display_name}")
        await ctx.send(embed=e)

    @command(name="docs", aliases=["d", "doc", "documentation"])
    async def docs_command(self, ctx: Context, key: str = None, *, query: str = None):
        """Sends documentation link for the given query"""
        if not key or key.lower() not in self.page_types.keys():
            query = key
            key = "py"

        await self.send_doc(ctx, key, query)
    
    @command(name="source", aliases=["src"])
    async def source_command(self, ctx: Context):
        embed = discord.Embed(title="Bot's GitHub Repository")
        embed.set_thumbnail(url=BotConfig.github_avatar_url)
        embed.add_field(name="Repository", value=f"[Go To GitHub]({BotConfig.github})")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Docs(bot))