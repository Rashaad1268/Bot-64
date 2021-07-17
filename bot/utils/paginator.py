import discord, logging, typing as t

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
        items_per_page: t.Optional[int] = 8,
        letters_per_page: t.Optional[int]=1998,
        empty_footer: t.Optional[bool] = True,
    ):

        super().__init__(
            timeout=timeout, delete_message_after=False, clear_reactions_after=True
        )

        self.pages : t.List[str]= pages
        self.initial_embed: discord.Embed = initial_embed
        self.footer_text: str = footer_text
        self.prefix: str = str(prefix) + "\n" if str(prefix) else str(prefix)
        self.suffix: str = "\n" + str(suffix) if str(suffix) else str(suffix)
        self.current_page: int = 0
        self.last_page: int = len(self.pages) - 1
        self.letters_per_page: int = letters_per_page
        self.items_per_page: int = items_per_page
        self.empty_footer: bool = empty_footer

        if not isinstance(self.pages, list):
            raise TypeError("pages need to be list")
        if not isinstance(self.items_per_page, int):
            raise TypeError("items_per_page need to be int")
        if not isinstance(self.letters_per_page, int):
            raise TypeError("letters_per_page need to be int")

    def add_page(self, content: str):
        letters_per_page = self.letters_per_page

        for i in range(0, len(content), letters_per_page):
            self.pages.append(content[i:i+letters_per_page])


    def format_pages(self, pages: t.List[str]):
        for i in range(0, len(pages), self.items_per_page):
            next_pages = pages[i : i + self.items_per_page]
            page_entry = ""

            for some_page in next_pages:
                page_entry += some_page + "\n"

            for x in [
                page_entry[i : i + self.letters_per_page]
                for i in range(0, len(page_entry), self.letters_per_page)
            ]:
                self.add_page(x)

    def add_line(self, content: str):
        try:
            if len(self.pages[self.last_page]) >= self.letters_per_page:
                self.add_page(content)
            else:
                if (
                    len(self.pages[self.last_page]) + len(content)
                    >= self.letters_per_page
                ):
                    self.add_page(
                        content[: len(self.pages[self.last_page]) - len(content)]
                        + "..."
                    )
                    self.add_line(
                        "..."
                        + content[len(self.pages[self.last_page]) - len(content) :]
                    )
                else:
                    self.pages[self.last_page] += content

        except IndexError:
            if len(content) >= self.letters_per_page:
                self.add_page(content[: self.letters_per_page] + "...")
                self.add_line("..."+content[self.letters_per_page - len(content) :])

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
        elif self.empty_footer and len(self.pages) == 1:
            pass
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
        if self.pages == []:
            raise EmptyPaginatorError("There are no pages supplied to paginate")

        else:
            all_pages = self.pages
            self.pages = []
            self.format_pages(all_pages)
            await super().start(ctx)

            if len(self.pages) <= 1:
                self.stop()

    async def start(self, ctx):
        raise NotImplementedError(
            f"Use CustomPaginator.paginate() instead of CustomPaginator.start()"
        )
