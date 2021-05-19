import discord, io, time, typing as t

from matplotlib import pyplot as plt
from discord.ext import commands
from discord.ext.commands import Context, command, Cog, cooldown, group

from bot.main import Bot
from bot.utils.paginator import CustomPaginator
from bot.utils.checks import is_staff, in_valid_channels
from bot.constants import Colours, WeatherApi


class FunCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name="binary", aliases=["bin"])
    @in_valid_channels()
    async def convert_to_binary(self, ctx, *, chars):
        """Converts the given arguments to binary"""
        result = " ".join(format(ord(x), "b") for x in chars)
        embed = discord.Embed(
            title="Here is the result converted to binary",
            colour=Colours.random(),
        )
        await CustomPaginator(
            pages=[result[i : i + 2000] for i in range(0, len(result), 2000)],
            initial_embed=embed,
            prefix="```powershell\n",
            suffix="```",
        ).paginate(ctx)

    @command(name="paginator", aliases=["pag"])
    @is_staff()
    async def paginate_command(self, ctx, items_per_page: int,*args):
        if args:
            await CustomPaginator(pages=[*args]).paginate(ctx)
        else:
            return await ctx.send("No pages supplied to paginate")

    @command(name="weather")
    @in_valid_channels()
    @cooldown(3, 120, commands.BucketType.user)
    async def show_weather(self, ctx, *, location: str):
        querystring = {"q": location, "lang": "en", "mode": "json"}
        headers = {
            "x-rapidapi-key": WeatherApi.api_key,
            "x-rapidapi-host": WeatherApi.api_host,
        }

        async with self.bot.http_session.get(
            WeatherApi.api_url, headers=headers, params=querystring
        ) as response:
            raw_json_data = await response.json()

        if raw_json_data["cod"]:
            if int(raw_json_data["cod"]) == 404:
                embed = discord.Embed(
                    title="Incorrect Location",
                    description=f"{location} is an incorrect location",
                    colour=Colours.red,
                )
                return await ctx.send(embed=embed)

        coordinates = raw_json_data["coord"]
        weather = raw_json_data["weather"]
        main = raw_json_data["main"]
        _sys = raw_json_data["sys"]
        clouds = raw_json_data["clouds"]
        wind = raw_json_data["wind"]
        city_name = raw_json_data["name"]

        LOCATION_MESSAGE = f"""
Location info
Country: {_sys['country']}
Name: {city_name}
City coordinates: latitudes {coordinates['lat']}, longitudes {coordinates['lon']}\n
Weather Info
Mainly: {weather[0]['main']}
Description: {weather[0]['description']}
Temperature: {main['temp']} kelvin
Feels like: {main['feels_like']} kelvin
Minimum Temperature: {main['temp_min']} kelvin
Max Temperature: {main['temp_max']} kelvin
Humidity: {main['humidity']} kelvin
Pressure: {main['pressure']}
Clouds: {clouds['all']}\n
Wind info
Wind speed: {wind['speed']}
Wind deg: {wind['deg']}"""

        embed = discord.Embed(
            title=f"Weather info for {location}",
            description=LOCATION_MESSAGE,
            colour=Colours.light_blue,
            timestamp=ctx.message.created_at,
        )
        embed.set_footer(text=f"Requested by {str(ctx.author)}")
        await ctx.send(embed=embed)

    @group(name="plot", invoke_without_command=True)
    async def plot_command(self, ctx, *points):
        """Plots the given coordinates according to the given style"""
        await ctx.send_help(ctx.command)

    @plot_command.command(name="chart")
    async def plot_chart(self, ctx, *args):
        """Sends a chart plot of the given coordinates"""
        plt.figure()
        plt.plot([arg for arg in args])
        plt.title("Plot")
        with io.BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            plot_file = discord.File(buffer, filename="chart_plot.png")
            await ctx.send(f"{ctx.author.mention} Here is your plot", file=plot_file)

    @plot_command.command(name="pie")
    async def plot_pie(self, ctx, *args):
        """Sends a pie plot of the given coordinates"""
        plt.pie([arg for arg in args], autopct="%1.1f%%")
        plt.title("Pie chart")

        with io.BytesIO() as buffer:
            plt.savefig(buffer, format="png")
            buffer.seek(0)
            plot_file = discord.File(buffer, filename="pie_plot.png")
            await ctx.send(f"{ctx.author.mention} Here is your plot", file=plot_file)

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket and API latency."""
        start_time = time.time()
        message = await ctx.send("Testing Ping...")
        end_time = time.time()

        await message.edit(
            content=f"Pong!\n{round(self.bot.latency * 1000)}ms\nAPI: {round((end_time - start_time) * 1000)}ms"
        )


def setup(bot: Bot):
    bot.add_cog(FunCommands(bot))
