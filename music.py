import asyncio
import logging

import discord
import yt_dlp
from discord import app_commands

log = logging.getLogger(__name__)

queues = {}
# 길드별 볼륨. 다음 곡으로 넘어가도 설정이 유지되도록 따로 들고 있는다.
volumes = {}
DEFAULT_VOLUME = 0.1


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]


YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


def _first_entry(data):
    """검색 결과에서 첫 번째 항목을 꺼낸다."""
    if data is None:
        raise ValueError("검색 결과가 없어요!")
    if "entries" in data:
        entries = [e for e in data["entries"] if e]
        if not entries:
            raise ValueError("검색 결과가 없어요!")
        return entries[0]
    return data


async def fetch_track(query):
    """대기열에 넣을 곡 정보를 미리 가져온다.

    스트림 주소는 시간이 지나면 만료되므로 여기서는 제목과 영상 주소만 챙기고,
    실제 재생 주소는 재생 직전에 다시 뽑는다.
    """
    data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))
    entry = _first_entry(data)
    return {
        "title": entry.get("title") or query,
        "url": entry.get("webpage_url") or entry.get("original_url") or query,
    }


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=DEFAULT_VOLUME):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        data = _first_entry(data)
        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


def setup_music_commands(bot):
    async def announce(channel, embed):
        """채널 전송 권한이 없어도 봇이 죽지 않도록 감싼다."""
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as e:
            log.warning("채널 전송 실패: %s", e)

    def not_connected_embed():
        embed = discord.Embed(
            title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600
        )
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        return embed

    def other_channel_embed(channel):
        embed = discord.Embed(
            title="다른 음성 채널에서 재생 중이에요!",
            description=f"{channel.mention} 으로 와주세요!",
            color=0x7AA600,
        )
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        return embed

    async def leave(guild):
        """음성 채널에서 나가고 대기열을 정리한다."""
        queues.pop(guild.id, None)
        if guild.voice_client is not None:
            try:
                await guild.voice_client.disconnect()
            except discord.HTTPException as e:
                log.warning("음성 채널 연결 해제 실패: %s", e)

    def has_human(channel):
        """채널에 봇이 아닌 사람이 남아 있는지 확인한다.

        channel.members는 멤버 캐시(members 인텐트)에 의존해 비어 보일 수 있으므로
        캐시와 무관한 voice_states를 직접 센다.
        """
        for user_id in channel.voice_states:
            if user_id == bot.user.id:
                continue
            member = channel.guild.get_member(user_id)
            if member is None or not member.bot:
                return True
        return False

    @bot.event
    async def on_voice_state_update(member, before, after):
        guild = member.guild
        vc = guild.voice_client

        # 봇 자신이 채널에서 나갔거나 쫓겨난 경우 대기열을 비운다.
        if member.id == bot.user.id and after.channel is None:
            queues.pop(guild.id, None)
            return

        if vc is None or vc.channel is None:
            return
        # 봇이 있는 채널에서 누군가 빠져나간 상황만 확인한다.
        if before.channel != vc.channel or after.channel == vc.channel:
            return
        if has_human(vc.channel):
            return
        log.info("%s 채널에 아무도 없어 나갑니다.", vc.channel.name)
        await leave(guild)

    @bot.event
    async def on_guild_remove(guild):
        # 서버에서 쫓겨나거나 나갔을 때 남은 데이터를 정리한다.
        queues.pop(guild.id, None)
        volumes.pop(guild.id, None)

    @bot.tree.command(name="join", description="음성 채널에 연결해요!")
    @app_commands.guild_only()
    async def join_channel(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is not None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"이미 {vc.channel.mention} 에 있어요!", color=0x7AA600
                ),
                ephemeral=True,
            )
            return
        if interaction.user.voice is None:
            await interaction.response.send_message(
                embed=not_connected_embed(), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.user.voice.channel.connect()
        except (
            discord.ClientException,
            asyncio.TimeoutError,
            discord.HTTPException,
        ) as e:
            log.warning("음성 채널 연결 실패: %s", e)
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"음성 채널에 연결하지 못했어요: {str(e)}",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            embed=discord.Embed(description="연결했어요!", color=0x7AA600),
            ephemeral=True,
        )

    @bot.tree.command(name="quit", description="음성 채널에서 떠나요!")
    @app_commands.guild_only()
    async def quit_channel(interaction: discord.Interaction):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message(
                embed=not_connected_embed(), ephemeral=True
            )
            return
        await leave(interaction.guild)
        await interaction.response.send_message(
            embed=discord.Embed(description="나갔어요!", color=0x7AA600),
            ephemeral=True,
        )

    @bot.tree.command(name="add", description="대기열에 노래를 추가해요!")
    @app_commands.guild_only()
    async def add_music(interaction: discord.Interaction, title: str):
        vc = interaction.guild.voice_client
        user_channel = (
            interaction.user.voice.channel if interaction.user.voice else None
        )
        if vc is None and user_channel is None:
            await interaction.response.send_message(
                embed=not_connected_embed(), ephemeral=True
            )
            return
        # 봇이 이미 다른 채널에 있으면 엉뚱한 곳에서 재생되지 않게 막는다.
        if vc is not None and user_channel is not None and vc.channel != user_channel:
            await interaction.response.send_message(
                embed=other_channel_embed(vc.channel), ephemeral=True
            )
            return

        # 음성 연결과 노래 검색이 3초를 넘길 수 있어 먼저 응답을 유예한다.
        await interaction.response.defer(ephemeral=True)
        if vc is None:
            try:
                await user_channel.connect()
            except (
                discord.ClientException,
                asyncio.TimeoutError,
                discord.HTTPException,
            ) as e:
                log.warning("음성 채널 연결 실패: %s", e)
                await interaction.followup.send(
                    embed=discord.Embed(
                        description=f"음성 채널에 연결하지 못했어요: {str(e)}",
                        color=0xFF0000,
                    ),
                    ephemeral=True,
                )
                return

        # 제목을 미리 확인해 두면 /queue에 검색어 대신 실제 곡 이름이 보이고,
        # 재생으로 넘어갈 때 검색 단계를 건너뛸 수 있다.
        try:
            track = await fetch_track(title)
        except Exception as e:
            log.warning("곡 검색 실패(%s): %s", title, e)
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"노래를 찾지 못했어요: {str(e)}", color=0xFF0000
                ),
                ephemeral=True,
            )
            return

        get_queue(interaction.guild.id).append(track)
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"대기열에 **{track['title']}** 추가완료!", color=0x7AA600
            ),
            ephemeral=True,
        )

        vc = interaction.guild.voice_client
        # 일시정지 상태에서는 is_playing()이 False라 그대로 두어야 한다.
        if vc is not None and not (vc.is_playing() or vc.is_paused()):
            await play_music(interaction, bot)

    async def play_music(interaction: discord.Interaction, bot):
        guild = interaction.guild
        # 재생에 실패한 곡을 건너뛸 때 재귀 대신 반복문을 쓴다.
        while True:
            vc = guild.voice_client
            if vc is None or not vc.is_connected():
                # /quit 이나 자동 퇴장으로 이미 나간 뒤 after 콜백이 도착한 경우
                queues.pop(guild.id, None)
                return

            queue = get_queue(guild.id)
            if not queue:
                embed = discord.Embed(
                    title="대기중인 노래들이 없어요!",
                    description="/add 명령어로 노래를 추가해봐요!",
                    color=0x7AA600,
                )
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await announce(interaction.channel, embed)
                return

            track = queue.pop(0)
            try:
                player = await YTDLSource.from_url(
                    track["url"], loop=bot.loop, stream=True
                )
            except Exception as e:
                log.warning("재생 준비 실패(%s): %s", track["title"], e)
                await announce(
                    interaction.channel,
                    discord.Embed(
                        description=f"**{track['title']}** 재생 중 오류 발생: {str(e)}",
                        color=0xFF0000,
                    ),
                )
                # 실패한 곡은 건너뛰고 다음 곡을 시도한다.
                continue

            player.volume = volumes.get(guild.id, DEFAULT_VOLUME)

            def after_play(error):
                if error:
                    log.error("재생 중 오류: %s", error)
                # after 콜백은 오디오 스레드에서 호출되므로 스레드 안전하게 넘긴다.
                asyncio.run_coroutine_threadsafe(play_music(interaction, bot), bot.loop)

            try:
                vc.play(player, after=after_play)
            except discord.ClientException as e:
                log.warning("재생 시작 실패: %s", e)
                await announce(
                    interaction.channel,
                    discord.Embed(
                        description=f"노래를 재생하지 못했어요: {str(e)}",
                        color=0xFF0000,
                    ),
                )
                return

            embed = discord.Embed(
                title=":musical_note: 지금 플레이 중인 노래!",
                description=player.title or track["title"],
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            await announce(interaction.channel, embed)
            return

    @bot.tree.command(name="queue", description="노래 대기열을 보여줘요!")
    @app_commands.guild_only()
    async def music_queue(interaction: discord.Interaction):
        queue = get_queue(interaction.guild.id)
        if queue:
            lines = [f"{n}. {t['title']}" for n, t in enumerate(queue, start=1)]
            embed = discord.Embed(
                title="대기중인 노래들이에요!",
                description="\n".join(lines)[:4096],
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        else:
            embed = discord.Embed(
                title="대기중인 노래들이 없어요!",
                description="/add 명령어로 노래를 추가해봐요!",
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="skip", description="노래를 스킵해요!")
    @app_commands.guild_only()
    async def skip_music(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            await interaction.response.send_message(
                embed=not_connected_embed(), ephemeral=True
            )
            return
        if not (vc.is_playing() or vc.is_paused()):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="재생 중인 노래가 없어요!", color=0x7AA600
                ),
                ephemeral=True,
            )
            return
        vc.stop()
        await interaction.response.send_message(
            embed=discord.Embed(description="스킵완료!", color=0x7AA600),
            ephemeral=True,
        )

    @bot.tree.command(name="pause", description="노래를 일시정지/재개해요!")
    @app_commands.guild_only()
    async def pause_music(interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            await interaction.response.send_message(
                embed=not_connected_embed(), ephemeral=True
            )
            return
        if vc.is_playing():
            vc.pause()
            message = "일시정지 완료!"
        elif vc.is_paused():
            vc.resume()
            message = "재개 완료!"
        else:
            message = "재생 중인 노래가 없어요!"
        await interaction.response.send_message(
            embed=discord.Embed(description=message, color=0x7AA600), ephemeral=True
        )

    @bot.tree.command(name="volume", description="볼륨을 변경해요!")
    @app_commands.guild_only()
    async def volume_change(interaction: discord.Interaction, volume: int):
        if not (0 <= volume <= 100):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="볼륨은 0에서 100 사이여야 해요!", color=0x7AA600
                ),
                ephemeral=True,
            )
            return
        # 설정은 다음 곡에도 이어지도록 길드별로 기억해 둔다.
        volumes[interaction.guild.id] = volume / 100

        vc = interaction.guild.voice_client
        # 재생 중이 아니면 source가 None이라 지금 당장은 반영할 수 없다.
        if vc is not None and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = volume / 100
            message = f"볼륨을 {volume}%로 바꿨어요!"
        else:
            message = f"다음 노래부터 볼륨을 {volume}%로 틀어드릴게요!"
        await interaction.response.send_message(
            embed=discord.Embed(description=message, color=0x7AA600), ephemeral=True
        )
