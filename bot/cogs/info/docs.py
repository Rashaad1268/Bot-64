import io
import os
import re
import zlib

import aiohttp
import discord
from discord.ext import commands



PAGES = {
        "antispam": "https://dpy-anti-spam.readthedocs.io/en/latest",
        "discord.py": "https://discordpy.readthedocs.io/en/latest",
        "py": "https://docs.python.org/3",
        "asyncpg": "https://magicstack.github.io/asyncpg/current",
        "django": "https://docs.djangoproject.com/en/3.2/_objects"
}



# Sphinx reader pbject because d.py docs
# are written in sphinx.
class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer: bytes):
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
    
    def __iter__(self):
        buf = b''
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode()
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')


class Documentation(commands.Cog, name="Documentation"):
    def __init__(self, bot):
        self.bot = bot
        self.page_types = PAGES
        self.cache = {}

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
            async with self.bot.http_session.get(page + "/objects.inv") as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        "Cannot build rtfm lookup table, try again later."
                    )

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self.cache = cache

    async def do_rtfm(self, ctx, obj):
        page_types = self.page_types

        if not hasattr(self, "_rtfm_cache"):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        cache = liste.items())
        # print(cache)

        self.matches = self.finder(obj, cache, key=lambda t: t[0], lazy=False)

        e = discord.Embed(description=f"**Query:** `{obj}`\n\n", colour=0xCE2029, timestamp=ctx.message.created_at)
        if len(self.matches) == 0:
            return await ctx.send("Could not find anything. Sorry.")

        e.description += "\n".join(f"[`{key}`]({url})" for key, url in self.matches)
        e.set_footer(text=f"Requested by: {ctx.author.display_name}")
        await ctx.send(embed=e)

    @commands.command(
        name="docs",
        aliases=["d", "doc"],
    )
    async def docs_command(self, ctx, *, query: str):
        """Sends documentation for the given query"""

        await self.do_rtfm(ctx, query)


def setup(bot):
    bot.add_cog(Documentation(bot))
