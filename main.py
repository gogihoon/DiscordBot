import discord
import re
from discord import app_commands
from config import *
from music import setup_music_commands
from weather import setup_weather_commands
from steam import setup_steam_commands
from lol import setup_lol_commands


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)


intents = discord.Intents.default()
intents.message_content = True
bot = MyClient(intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name="음악"),
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if not message.content.startswith("/"):
        m = re.match(r"^<a?:[\w]+:([\d]+)>$", message.content)
        if m:
            ext = "gif" if message.content.startswith("<a:") else "png"
            embed = discord.Embed(color=0x7AA600)
            embed.set_author(
                name=message.author.display_name, icon_url=message.author.avatar.url
            )
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{m.group(1)}.{ext}")
            await message.channel.send(embed=embed)
            await message.delete()


# 기능별 명령어 등록
setup_music_commands(bot)
setup_weather_commands(bot)
setup_steam_commands(bot)
setup_lol_commands(bot)

bot.run(DISCORD_KEY)
