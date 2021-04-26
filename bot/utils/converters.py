import discord

from discord.ext import commands
from discord.ext.commands import Context, BadArgument, Converter


class Subreddit(Converter):
    """Forces a string to begin with "r/" and checks if it's a valid subreddit."""

    @staticmethod
    async def convert(ctx: Context, sub: str):
        """
        Force sub to begin with "r/" and check if it's a valid subreddit.
        If sub is a valid subreddit, return it prepended with "r/"
        """
        sub = sub.lower()

        if not sub.startswith("r/"):
            sub = f"r/{sub}"

        resp = await ctx.bot.http_session.get(
            "https://www.reddit.com/subreddits/search.json", params={"q": sub}
        )

        json = await resp.json()
        if not json["data"]["children"]:
            raise BadArgument(
                f"The subreddit `{sub}` either doesn't exist, or it has no posts."
            )

        return sub


class OffTopicName(Converter):
    """A converter that ensures an added off-topic name is valid."""

    ALLOWED_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!?'`-"

    @classmethod
    def translate_name(cls, name: str, *, from_unicode: bool = True) -> str:
        """
        Translates `name` into a format that is allowed in discord channel names.
        If `from_unicode` is True, the name is translated from a discord-safe format, back to normalized text.
        """
        if from_unicode:
            table = str.maketrans(cls.ALLOWED_CHARACTERS, '𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹ǃ？’’-')
        else:
            table = str.maketrans('𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹ǃ？’’-', cls.ALLOWED_CHARACTERS)

        return name.translate(table)

    async def convert(self, ctx: Context, argument: str) -> str:
        """Attempt to replace any invalid characters with their approximate Unicode equivalent."""
        # Chain multiple words to a single one
        argument = "-".join(argument.split())

        if not (2 <= len(argument) <= 50):
            raise BadArgument("Channel name must be between 2 and 50 chars long")

        elif not all(c.isalnum() or c in self.ALLOWED_CHARACTERS for c in argument):
            raise BadArgument(
                "Channel name must only consist of "
                "alphanumeric characters, minus signs or apostrophes."
            )

        # Replace invalid characters with unicode alternatives.
        return self.translate_name(argument)
