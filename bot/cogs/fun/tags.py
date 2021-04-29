import discord, typing as t, asyncio, random
from bot.database.tags_db import Tags as TagsDB
from bot.utils import checks, helpful, paginator

from bot.main import Bot
from bot.constants import Colours, POSITIVE_REPLIES, ERROR_REPLIES
from discord.ext import commands


class Tags(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.tags = TagsDB(self.bot)

    @commands.group(name="tags", aliases=["tag", "t"], invoke_without_command=True)
    async def tags_command(self, ctx, *, tag_name: t.Optional[str] = None):
        """The main tags command"""
        if not tag_name:
            await self.list_all_tags(ctx)
            return
        else:
            tag = await self.tags.get_tag(tag_name)
            if not tag:
                await ctx.send(
                    embed=helpful.build_error_embed(f"`{tag}` isn't a valid tag")
                )
                return

            else:
                embed = discord.Embed(title=tag['name'], colour=Colours.orange)
                embed.description = tag["content"]
                await ctx.send(embed=embed)

    @tags_command.command(name="create", aliases=("c",))
    @checks.is_staff()
    async def create_tag(self, ctx, *, tag_name: str):
        """Creates a tag"""
        if await self.tags.get_tag(tag_name):
            await ctx.send(
                embed=helpful.build_error_embed(f"`{tag_name}` is already a valid tag")
            )
            return

        else:
            try:
                tag_content = await helpful.get_reply(
                    ctx, "What will be the content of that tag?", timeout=300
                )
            except asyncio.TimeoutError:
                await ctx.message.reply(
                    embed=helpful.build_error_embed(
                        f"You took too long to respond, didn't create tag",
                        title="Time out",
                    )
                )
            tag_id = await self.tags.create(tag_name, tag_content, ctx.author)
            embed = discord.Embed(
                title=random.choice(POSITIVE_REPLIES),
                description=f"Created tag `{tag_name}`",
            )
            embed.set_footer(text=f"Tag ID: {tag_id}")
            await ctx.send(embed=embed)

    @tags_command.command(name="delete", aliases=("d", "del"))
    @checks.is_admin()
    async def delete_tag(self, ctx, *, tag_name: str):
        """Deletes a tag with the given name"""
        if await self.tags.get_tag(tag_name):
            await self.tags.delete(tag_name)
            return
        else:
            await ctx.send(
                embed=helpful.build_error_embed(
                    f"`{tag_name}` isn't a valid tag to delete"
                )
            )

    @tags_command.command(name="list", aliases=("l",))
    async def list_all_tags(self, ctx):
        """Lists all of the tags"""
        pages = []
        tags_per_page = 10
        all_tags = await self.bot.db.fetch("SELECT Id, Name FROM Tags")
        all_tags = [f"{tag['name']} (ID: {tag['id']})" for tag in all_tags]

        for i in range(0, len(all_tags), tags_per_page):
            next_tags = all_tags[i : i + tags_per_page]
            tags_entry = ""

            for _tag in next_tags:
                foratted = f"**»** {_tag}\n"

                tags_entry += foratted
            pages.append(tags_entry)

        embed = discord.Embed(title="All current tags", colour=Colours.python_blue)
        pag = paginator.CustomPaginator(
            pages, embed, "You can use !tag <tag_name> to view a tag"
        )
        await pag.paginate(ctx)

    @tags_command.command(name="search", aliases=("s",))
    async def search_tags(self, ctx, *, name: str):
        """Searches through the tags"""
        search_results = await self.tags.search(name)

        embed = discord.Embed(
            title="Search results",
            description=f"\n".join(
                [f"{tag['name']} (ID: {tag['id']})" for tag in search_results]
            ),
            colour=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @tags_command.command(name="text", aliases=("t",))
    async def send_tag_text(self, ctx, *, tag_name: str):
        """Sends a tag with the given name in plain text"""
        tag = await self.tags.get_tag(tag_name)

        if tag:
            await ctx.send(tag["content"])
        
        else:
            await ctx.send(embed=helpful.build_error_embed(f"`{tag_name}` isn't a valid tag"))
            return


def setup(bot: Bot):
    bot.add_cog(Tags(bot))
