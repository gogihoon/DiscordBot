#-*- coding:utf-8 -*- 
import asyncio
import discord
import youtube_dl
import neispy
import datetime
from discord.ext import commands

#쓰읍..
name="울산애니원고등학교"

neis = neispy.Client('***REMOVED***')

meal1='방학입니다'
meal2='방학입니다'
meal3='방학입니다'
scinfo = neis.schoolInfo(SCHUL_NM=name)
AE = scinfo[0].ATPT_OFCDC_SC_CODE  # 교육청코드
SE = scinfo[0].SD_SCHUL_CODE  # 학교코드
scschedule =neis.SchoolSchedule(AE, SE)
schedule = scschedule[0].EVENT_NM  # 학사일정명 가져옴
if schedule != '여름방학' and schedule != '겨울방학':
    scmeal = neis.mealServiceDietInfo(AE, SE)
    meal1 = scmeal[0].DDISH_NM.replace("<br/>", "\n")
    meal2 = scmeal[1].DDISH_NM.replace("<br/>", "\n")
    meal3 = scmeal[2].DDISH_NM.replace("<br/>", "\n")

youtube_dl.utils.bug_report_message=lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self,bot):
        self.bot=bot

    @commands.command()
    async def 도움말(self, ctx):
        await ctx.send("들어와,나가,노래")

    @commands.command()
    async def 영어(self, ctx, *, text1):
        await ctx.send(":regional_indicator_"+text1+":")


    
    @commands.command()
    async def 들어와(self, ctx, *, channel:discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def 노래(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'에러 : {e}') if e else None)

        await ctx.send(f':play_pause:지금 플레이 중인 노래 : {player.title}')

    @commands.command()
    async def 볼륨(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("음성 채널에 연결되있지 않습니다.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"볼륨을 {volume}%로 바꿨습니다.")

    @commands.command()
    async def 나가(self, ctx):
        await ctx.voice_client.disconnect()

    @노래.before_invoke
    async def ensure_voice(self, ctx):#노래 자동으로 와서 틀기
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("당신은 음성 채널에 연결되있지 않습니다.")
                raise commands.CommandError("사용자가 음성 채널에 없음.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
    @commands.command()
    async def 아침(self, ctx):
        await ctx.send(meal1);
    @commands.command()
    async def 점심(self, ctx):
        await ctx.send(meal2);
    @commands.command()
    async def 저녘(self, ctx):
        await ctx.send(meal3);



bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='wtf')
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message_delete(message):
    print(f"{message.content} 삭제됨")

@bot.event
async def on_message_edit(before, after):
    print(f"{before.content} 에서 {after.content} 로 편집됨.")

bot.add_cog(Music(bot))
bot.run('***REMOVED******REMOVED***')
