import logging
import re

import discord
from discord import app_commands

from config import BETA_KEY
from gemini import setup_gemini_commands
from lol import setup_lol_commands
from music import setup_music_commands
from steam import setup_steam_commands
from utils import Responder, crash_embed, error_embed
from weather import setup_weather_commands

log = logging.getLogger(__name__)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)


intents = discord.Intents.default()
intents.message_content = True
bot = MyClient(intents=intents)

synced = False


@bot.event
async def on_ready():
    # on_ready는 재연결할 때마다 불리므로 명령어 동기화는 한 번만 한다.
    global synced
    if not synced:
        try:
            await bot.tree.sync()
            synced = True
        except discord.HTTPException as e:
            log.error("명령어 동기화 실패: %s", e)
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.listening, name="음악"),
    )


@bot.tree.error
async def on_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    """각 명령의 try/except가 놓친 예외를 받는 마지막 그물."""
    reply = Responder(interaction)
    if isinstance(error, app_commands.NoPrivateMessage):
        await reply.send(
            error_embed("이 명령은 서버 안에서만 쓸 수 있어요!"), ephemeral=True
        )
        return
    if isinstance(error, app_commands.CommandOnCooldown):
        await reply.send(
            error_embed(f"조금만 천천히요! {error.retry_after:.0f}초 뒤에 다시 시도해 주세요."),
            ephemeral=True,
        )
        return

    command = interaction.command.name if interaction.command else "?"
    log.exception("/%s 처리 중 예외", command, exc_info=error)
    await reply.send(
        crash_embed("명령을 처리하지 못했어요. 잠시 후 다시 시도해 주세요."),
        ephemeral=True,
    )


@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None:
        return
    if message.content.startswith("/"):
        return
    m = re.match(r"^<a?:[\w]+:([\d]+)>$", message.content)
    if not m:
        return

    # 원본 메시지를 지울 수 없으면 이모티콘을 확대하지 않는다.
    perms = message.channel.permissions_for(message.guild.me)
    if not (perms.manage_messages and perms.send_messages and perms.embed_links):
        return

    ext = "gif" if message.content.startswith("<a:") else "png"
    embed = discord.Embed(color=0x7AA600)
    embed.set_author(
        name=message.author.display_name,
        icon_url=message.author.display_avatar.url,
    )
    embed.set_image(url=f"https://cdn.discordapp.com/emojis/{m.group(1)}.{ext}")
    try:
        await message.channel.send(embed=embed)
        await message.delete()
    except discord.HTTPException as e:
        log.warning("이모티콘 처리 실패: %s", e)


# 기능별 명령어 등록
setup_music_commands(bot)
setup_weather_commands(bot)
setup_steam_commands(bot)
setup_lol_commands(bot)
setup_gemini_commands(bot)

# 로깅은 logconf에서 이미 설정했으므로 discord.py가 다시 건드리지 않게 한다.
bot.run(BETA_KEY, log_handler=None)
