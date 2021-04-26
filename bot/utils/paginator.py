import discord, logging,  typing as t

from discord.ext import commands, menus  # pip install discord-ext-menus

from bot.constants import Emojis


log = logging.getLogger(__name__)

FIRST_PAGE = "\u23EE"
LEFT_PAGE = "\u2B05"
QUIT_PAGINATION = "\u23f9"
RIGHT_PAGE = "\u27A1"
LAST_PAGE = "\u23ED"

"""
WARNING
The below code is very messy
If you do not like ugly code please do not look at it"""


class EmptyPaginatorError(Exception):
    """This is the exception which will be raised if the paginator pages list is empty"""

    pass


class CustomPaginator(menus.Menu):
    """Each page must be supplied as a new item of a list."""

    def __init__(
        self,
        pages: t.List[str] = [],
        initial_embed: discord.Embed = discord.Embed(),  # Default is an empty embed
        footer_text: t.Optional[str] = None,
        timeout: t.Optional[int] = 300.0,
        prefix: t.Optional[str] = "",
        suffix: t.Optional[str] = "",
        words_per_page=2000,
    ):

        super().__init__(
            timeout=timeout, delete_message_after=False, clear_reactions_after=True
        )

        self.pages = pages
        self.initial_embed = initial_embed
        self.footer_text = footer_text
        self.prefix = prefix
        self.suffix = suffix
        self.current_page = 0
        self.last_page = len(self.pages) - 1
        self.words_per_page = words_per_page

    def add_page(self, content: str):
        if isinstance(self.pages, list):
            if len(content) <= self.words_per_page:
                self.pages.append(content)
            
            else:
                self.pages.append(content[self.words_per_page:])
                self.pages.append(content[:self.words_per_page])

        else:
            raise TypeError(f"pages needs to be a list")

    def add_line(self, content: str):
        try:
            if len(self.pages[self.last_page]) >= self.words_per_page:
                self.add_page(content)
            else:
                new_content = content.split()
                for word in content:
                    self.pages[self.last_page] += word
                    if len(self.pages[self.last_page]) >= 2000:
                        self.add_page(content)
        except IndexError:
            self.pages.append(content)

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        self.current_page = 0  # The first page
        embed = self.initial_embed
        embed.description = self.prefix + self.pages[self.current_page] + self.suffix

        if self.footer_text:
            embed.set_footer(
                text=f"{self.footer_text} (Page {self.current_page + 1}/{len(self.pages)})"
            )
        else:
            embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")

        return await channel.send(embed=self.initial_embed)

    @menus.button(FIRST_PAGE)
    async def show_first_page(self, payload):
        if self.current_page == 0:
            await self.message.remove_reaction(FIRST_PAGE, payload.member)

        else:
            await self.message.remove_reaction(FIRST_PAGE, payload.member)

            self.current_page = 0
            embed = self.initial_embed
            embed.description = (
                self.prefix + self.pages[self.current_page] + self.suffix
            )
            if self.footer_text:
                embed.set_footer(
                    text=f"{self.footer_text} (Page {self.current_page + 1}/{len(self.pages)})"
                )
            else:
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")

            await self.message.edit(embed=embed)

    @menus.button(LEFT_PAGE)
    async def show_left_page(self, payload):
        if self.current_page == 0:
            await self.message.remove_reaction(LEFT_PAGE, payload.member)

        else:
            await self.message.remove_reaction(LEFT_PAGE, payload.member)
            self.current_page -= 1
            embed = self.initial_embed
            embed.description = (
                self.prefix + self.pages[self.current_page] + self.suffix
            )
            if self.footer_text:
                embed.set_footer(
                    text=f"{self.footer_text} (Page {self.current_page + 1}/{len(self.pages)})"
                )
            else:
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")

            await self.message.edit(embed=embed)

    @menus.button(QUIT_PAGINATION)
    async def stop_pagination(self, payload):
        self.stop()

    @menus.button(RIGHT_PAGE)
    async def show_right_page(self, payload):
        if self.current_page == self.last_page:
            await self.message.remove_reaction(RIGHT_PAGE, payload.member)

        else:
            await self.message.remove_reaction(RIGHT_PAGE, payload.member)
            self.current_page += 1
            embed = self.initial_embed
            embed.description = (
                self.prefix + self.pages[self.current_page] + self.suffix
            )
            if self.footer_text:
                embed.set_footer(
                    text=f"{self.footer_text} (Page {self.current_page + 1}/{len(self.pages)})"
                )
            else:
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")

            await self.message.edit(embed=embed)

    @menus.button(LAST_PAGE)
    async def show_last_page(self, payload):
        if self.current_page == self.last_page:
            await self.message.remove_reaction(LAST_PAGE, payload.member)

        else:
            self.current_page = self.last_page
            await self.message.remove_reaction(LAST_PAGE, payload.member)
            embed = self.initial_embed
            embed.description = (
                self.prefix + self.pages[self.current_page] + self.suffix
            )

            if self.footer_text:
                embed.set_footer(
                    text=f"{self.footer_text} (Page {self.current_page + 1}/{len(self.pages)})"
                )
            else:
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")

            await self.message.edit(embed=embed)

    async def paginate(self, ctx: commands.Context):
        all_pages = self.pages
        self.pages = []

        for page in all_pages:
            self.add_line(page)

        if self.pages == []:
            raise EmptyPaginatorError("There are no pages supplied to paginate")

        await super().start(ctx)

        if len(self.pages) <= 1:
            self.stop()

    async def start(self, ctx):
        raise NotImplementedError(
            f"Use CustomPaginator.paginate instead of CustomPaginator.start"
        )
