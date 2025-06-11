import discord
from discord import app_commands
import yt_dlp
import asyncio

queues = {}


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]


YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}
FFMPEG_OPTIONS = {"options": "-vn"}
ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if "entries" in data:
            data = data["entries"][0]
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


def setup_music_commands(bot):
    @bot.tree.command(name="join", description="음성 채널에 연결해요!")
    async def join_channel(interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
                await interaction.response.send_message(
                    embed=discord.Embed(description="연결했어요!", color=0x7AA600),
                    ephemeral=True,
                )
            else:
                embed = discord.Embed(
                    title="채널에 연결되지 않았어요!",
                    description="ㅠㅠ",
                    color=0x7AA600,
                )
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="quit", description="음성 채널에서 떠나요!")
    async def quit_channel(interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            embed = discord.Embed(
                title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message(
                embed=discord.Embed(description="나갔어요!", color=0x7AA600),
                ephemeral=True,
            )

    @bot.tree.command(name="add", description="대기열에 노래를 추가해요!")
    async def add_music(interaction: discord.Interaction, title: str):
        queue = get_queue(interaction.guild.id)
        if interaction.guild.voice_client is None:
            if interaction.user.voice:
                await interaction.user.voice.channel.connect()
            else:
                embed = discord.Embed(
                    title="채널에 연결되지 않았어요!",
                    description="ㅠㅠ",
                    color=0x7AA600,
                )
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        queue.append(title)
        await interaction.response.send_message(
            embed=discord.Embed(description="대기열에 추가완료!", color=0x7AA600),
            ephemeral=True,
        )
        if not interaction.guild.voice_client.is_playing():
            await play_music(interaction, bot)

    async def play_music(interaction: discord.Interaction, bot):
        queue = get_queue(interaction.guild.id)
        if not queue:
            embed = discord.Embed(
                title="대기중인 노래들이 없어요!",
                description="/add 명령어로 노래를 추가해봐요!",
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.channel.send(embed=embed)
        else:
            title = queue.pop(0)
            try:
                player = await YTDLSource.from_url(title, loop=bot.loop, stream=True)
            except Exception as e:
                await interaction.channel.send(
                    embed=discord.Embed(
                        description=f"노래 재생 중 오류 발생: {str(e)}", color=0xFF0000
                    )
                )
                return
            vc = interaction.guild.voice_client
            vc.play(
                player,
                after=lambda e: bot.loop.create_task(play_music(interaction, bot)),
            )
            embed = discord.Embed(
                title=":musical_note: 지금 플레이 중인 노래!",
                description=player.title,
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            await interaction.channel.send(embed=embed)

    @bot.tree.command(name="queue", description="노래 대기열을 보여줘요!")
    async def music_queue(interaction: discord.Interaction):
        queue = get_queue(interaction.guild.id)
        if queue:
            queue_list = " :arrow_forward: ".join(queue)
            embed = discord.Embed(
                title="대기중인 노래들이에요!", description=queue_list, color=0x7AA600
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="대기중인 노래들이 없어요!",
                description="/add 명령어로 노래를 추가해봐요!",
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="skip", description="노래를 스킵해요!")
    async def skip_music(interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            embed = discord.Embed(
                title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message(
                embed=discord.Embed(description="스킵완료!", color=0x7AA600),
                ephemeral=True,
            )

    @bot.tree.command(name="pause", description="노래를 일시정지/재개해요!")
    async def pause_music(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            embed = discord.Embed(
                title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if vc.is_playing():
                vc.pause()
                await interaction.response.send_message(
                    embed=discord.Embed(description="일시정지 완료!", color=0x7AA600),
                    ephemeral=True,
                )
            else:
                vc.resume()
                await interaction.response.send_message(
                    embed=discord.Embed(description="재개 완료!", color=0x7AA600),
                    ephemeral=True,
                )

    @bot.tree.command(name="volume", description="볼륨을 변경해요!")
    async def volume_change(interaction: discord.Interaction, volume: int):
        if not (0 <= volume <= 100):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="볼륨은 0에서 100 사이여야 해요!", color=0x7AA600
                ),
                ephemeral=True,
            )
            return
        vc = interaction.guild.voice_client
        if vc is None or not hasattr(vc, "source"):
            embed = discord.Embed(
                title="음성 채널에 연결되지 않았어요!",
                description="ㅠㅠ",
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            vc.source.volume = volume / 100
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"볼륨을 {volume}%로 바꿨어요!", color=0x7AA600
                ),
                ephemeral=True,
            )
