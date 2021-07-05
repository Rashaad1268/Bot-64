import discord

from discord.ext import commands

from bot.main import Bot
from bot.utils.paginator import CustomPaginator


class CustomHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command: commands.Command, show_help: bool=True):
        nl = "\n"
        return f"""```{self.clean_prefix}{command.qualified_name} {command.signature}```{'*'+command.help+'*' if command.help else 'This command does not have a description'}
                {'**You can also use: `'+'`, `'.join(command.aliases)+f'`**{nl}' if command.aliases and show_help else ""}""".strip()

    async def send_bot_help(self, mapping):
        pages = []
        embed = discord.Embed(title="Help", colour=discord.Colour.blurple())
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c, False) for c in filtered]
            cog_name = getattr(cog, "qualified_name", "No Category")
            pages.append(f"**{cog_name}**")
            for cmd_sig in command_signatures:
                pages.append(cmd_sig)
            pages[-1] += "\n"
        pag = CustomPaginator(pages=pages, initial_embed=embed, items_per_page=7)

        await pag.paginate(self.context)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f"Help", colour=discord.Colour.blurple())
        pag = CustomPaginator(pages=[], initial_embed=embed)
        pag.add_page(self.get_command_signature(command))

        await pag.paginate(self.context)

    async def send_cog_help(self, cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        cog_commands = [self.get_command_signature(c, False) for c in filtered]

        pages = [f"**Category {cog.qualified_name}**"]
        embed = discord.Embed(title=f"Help", colour=discord.Colour.blurple())

        for command in cog_commands:
            pages.append(command )

        pag = CustomPaginator(pages, embed, items_per_page=6)
        await pag.paginate(self.context)

    async def send_group_help(self, group):
        sub_commands = [c for c in await self.filter_commands(group.walk_commands(), sort=True)]
        embed = discord.Embed(title=f"Help", colour=discord.Colour.blurple())
        pages = [f"**Group {group.qualified_name}**\n{self.get_command_signature(group)}\n\n**Sub commands**"]


        for command in sub_commands:
            pages.append(f"`{self.clean_prefix}{command.qualified_name}`\n*{command.help}*")

        pag =  CustomPaginator(pages, embed, items_per_page=6)
        await pag.paginate(self.context)


def setup(bot: Bot):
    bot.help_command = CustomHelpCommand()
