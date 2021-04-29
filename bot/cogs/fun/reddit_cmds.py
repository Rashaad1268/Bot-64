import discord, asyncpraw, random, logging, asyncio
import typing as t

from discord.ext import commands
from discord.ext.commands import command, is_owner
from discord.ext import tasks

from bot.main import Bot
from bot.utils.checks import is_staff, in_valid_channels
from bot.constants import Colours, RedditAPI
from bot.utils.helpful import build_error_embed
from bot.utils.converters import Subreddit

log = logging.getLogger(__name__)
SUBBREDDIT_OPTIONS = ["memes", "wallstreetbets", "danidev", "programmerhumor"]


class RedditCog(commands.Cog, name="Reddit"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.submissions = []

    async def send_meme(self, ctx):
        async with ctx.typing():
            reddit = asyncpraw.Reddit(
                client_id=RedditAPI.client_id,
                client_secret=RedditAPI.client_secret,
                user_agent=RedditAPI.user_agent,
            )
            reddit.read_only = True

            random_subreddit = random.choice(SUBBREDDIT_OPTIONS)
            subreddit = await reddit.subreddit(random_subreddit)

            if self.submissions == []:
                await ctx.send(
                    embed=build_error_embed(
                        "Meme cache is empty\nRefreshing it... (This may take some time)\n"
                        "Please use this command after about 15 seconds",
                        title="No memes...For now"
                    ),
                )
                await self.refresh_submissions(ctx, 40)
                await ctx.send
                return

            post = random.choice(self.submissions)

            embed = discord.Embed(
                description=f"**[{post.title}](https://reddit.com{post.permalink})**",
                colour=Colours.random(),
            )
            embed.set_footer(text=f"👍 {post.score} | 💬 {len(await post.comments())}")
            if post.url:
                embed.set_image(url=post.url)

        await ctx.message.reply(embed=embed, mention_author=False)

    @command(name="meme", aliases=["m"])
    @is_staff()
    async def _meme(self, ctx):
        """Sends a random meme from reddit"""
        await self.send_meme(ctx)

    @commands.group(name="reddit", invoke_without_command=True)
    @is_owner()
    async def _reddit(self, ctx):
        await ctx.send_help(ctx.command)

    @_reddit.command(name="refresh")
    @is_owner()
    async def refresh_submissions(self, ctx, submission_count: int = 20):
        embed = discord.Embed(colour=Colours.orange)
        log.info("Updating reddit submissions")
        if len(self.submissions) >= 170:
            log.info(
                f"Cleared meme cache because it has more than 130 items ({len(self.submissions)})"
            )
            self.submissions = []

        reddit = asyncpraw.Reddit(
            client_id=RedditAPI.client_id,
            client_secret=RedditAPI.client_secret,
            user_agent=RedditAPI.user_agent,
        )
        reddit.read_only = True

        random_subreddit = random.choice(SUBBREDDIT_OPTIONS)
        embed.description = (
            f"Refreshing reddit submissions\nSubreddit: {random_subreddit}"
        )
        await ctx.send(embed=embed)
        subreddit = await reddit.subreddit(random_subreddit)

        async for submission in subreddit.top(limit=submission_count):
            await submission.load()
            self.submissions.append(submission)
            log.info("Added a submission to the submission cache")
            # yield submission

        log.info("Updated submissions successfully!")

    @_reddit.command(name="add-subreddit", aliases=["add-sub"])
    @is_owner()
    async def add_subbreddit(self, ctx, subreddit: Subreddit):
        SUBBREDDIT_OPTIONS.append(subreddit)

        embed = discord.Embed(
            description=f"Added {subreddit} subreddit to the subreddit options\nCurrent subreddit options: {SUBBREDDIT_OPTIONS}",
            colour=Colours.grass_green,
        )
        await ctx.send(embed=embed)

    @_reddit.command()
    @is_owner()
    async def remove_subbreddit(self, ctx, subreddit: Subreddit):
        SUBBREDDIT_OPTIONS.remove(subreddit)

        embed = discord.Embed(
            description=f"Removed {subreddit} subreddit from the subreddit options\nCurrent subreddit options: {SUBBREDDIT_OPTIONS}",
            colour=Colours.grass_green,
        )


def setup(bot: Bot):
    bot.add_cog(RedditCog(bot))
