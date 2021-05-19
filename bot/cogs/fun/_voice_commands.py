import discord
from discord.ext import commands
from discord.ext.commands import command, is_owner
import io
from gtts import gTTS # pip install gTTS

"""
This extension won't be loaded
Because the gtts module is blocking
and discord.py doesn't support playing BytesIO objects in voice channels
"""

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    @is_owner()
    async def join(self, ctx, *, vc: discord.VoiceChannel = None):
        """Joins a voice channel"""
        vc = vc or ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(vc)
            await ctx.message.add_reaction("👌")

        else:
            await vc.connect()
            await ctx.message.add_reaction("👌")

    @command()
    @is_owner()
    async def leave(self, ctx):
        """Leaves the voice channel"""
        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction("👋")

    @command(name="talk", aliases=["tl"])
    @is_owner()
    async def _talk(self, ctx, *, msg: str):
        from tempfile import TemporaryFile
        
        buffer = io.BytesIO()
        tts = gTTS(msg, lang="en")
        tts.write_to_fp(buffer)
        buffer.seek(0)

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(buffer))

        if ctx.voice_client:
            ctx.voice_client.play(
                source, after=lambda e: print(f"Player error: {e}") if e else None
            )

        else:
            await ctx.send("Not connected to voice")


def setup(bot):
    bot.add_cog(VoiceCommands(bot))
