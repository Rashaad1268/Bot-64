import discord
import typing as t
from pathlib import Path
from discord.ext import commands

from bot.main import Bot
from bot.utils.checks import is_staff

rules = [
"""
You must abide Discord Terms of Service.
Which can be found [here](https://discord.com/terms)
""",
"""
You cannot break the terms of service of any company.
- Or talking about stuff that can break it.""",
"""Bad behaviour is not accepted.
- Behave nicely.""",
"""
Please respect all members of the server, especially staff.
- When staff tells you to stop doing something stop it""",
"""
Do not ask for gifts, codes, accounts, money, etc.""",
"""
If there is a staff member in chat, please let them handle moderating the chat.""",
"""
Do not impersonate Staff Members, Friends, Content Creators, Bots, etc.""",
"""
If you want to contact the staff DM <@!803137010419105792>, or if <@!803137010419105792> is offline DM a staff member.""",
"""
If an incident is happening ping <@&803539777835499547> and the Moderators will handle it.""",
"""
Do not send any http links only send https links.""",
"""
No advertising
- This includes ANY DM advertisement, and also Discord invite links in the server""",
"""
Do not spam.
- Do not send messages with a short interval.
sending messages with a short interval may trigger <@780768428587614258> spam detection.""",
"""
Please try to keep conversations in English for better communication.""",
"""
If a bot gives an error inform the staff team and don't redo the action which caused the error.""",
]

RULES_NOTE = """
- All rules are subject to change at any time without notice
- All server rules apply in voice channels and events
- It is your responsibility to be aware of the rules and follow them
- All punishments are at the discretion of the Staff

If you have questions, ask a staff member."""


class Rules(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def rule(self, ctx, rule_number: int = None):
        """Sends the given server rule."""
        if not rule_number:
            await ctx.send("You must specify a rule number.")
            return

        if rule_number <= 0:  # Because negative indexing is possible.
            await ctx.send("Invalid rule number.")
            return  # To stop the program from doing anything else.

        try:
            rule_embed = discord.Embed(color=discord.Color.blurple())
            rule_embed.add_field(
                name=f"**Rule {rule_number}**", value=str(rules[rule_number - 1])
            )
            await ctx.send(embed=rule_embed)

        except IndexError:
            await ctx.send(f"Rule {rule_number} doesn't exists.")

    @rule.command()
    async def note(self, ctx):
        """Sends the rules server note"""
        note_embed = discord.Embed(color=discord.Color.blurple())
        note_embed.add_field(name="__**Please Note**__", value=RULES_NOTE)
        await ctx.send(embed=note_embed)

    @commands.command(name="send-rules", aliases=['send-rule'])
    @is_staff()
    async def send_rules(self, ctx, channel: t.Optional[discord.TextChannel]=None):
        channel = channel or ctx.channel
        rules_file = Path(r"C:\Users\Rushda Niyas\Desktop\Rashaad\bot_64_V2\server_rules.txt").read_text()
        rules_embed = discord.Embed(
            color=discord.Color.green(),
            title="Server rules",
            description=str(rules_file)
        )
        await channel.send(embed=rules_embed)


def setup(bot: Bot):
    bot.add_cog(Rules(bot))
