#-*- coding:utf-8 -*- 
import asyncio
import discord
import youtube_dl
import neispy
import datetime
import ctypes
import ctypes.util
import json
import requests
from discord.ext import commands

name="울산애니원고등학교"#급식 학교 이름
api_key = "***REMOVED******REMOVED***"#라이엇 api 키
neis = neispy.Client('***REMOVED***')#네이스 api 키

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
        await ctx.send("들어와\n나가\n노래 [노래제목]\n아침\n점심\n저녘\n")

    @commands.command()
    async def 영어(self, ctx, *, text1):
        await ctx.send(":regional_indicator_"+text1+":")


    
    @commands.command()
    async def 들어와(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("당신은 음성 채널에 연결되있지 않습니다.")
                raise commands.CommandError("사용자가 음성 채널에 없음.")

    @commands.command()
    async def 노래(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'에러 : {e}') if e else None)

        await ctx.send(f' :play_pause: 지금 플레이 중인 노래 : {player.title}')

    @commands.command()
    async def 볼륨(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("음성 채널에 연결되있지 않습니다.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"볼륨을 {volume}%로 바꿨습니다.")

    @commands.command()
    async def 나가(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def 멈춰(self, ctx):
        ctx.voice_client.stop()

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

    @commands.command()
    async def 롤전적(self, ctx, *, name):
        URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/"+name
        res = requests.get(URL, headers={"X-Riot-Token": api_key})
        if res.status_code == 200:
            #코드가 200일때
            resobj = json.loads(res.text)
            URL = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/"+resobj["id"]
            res = requests.get(URL, headers={"X-Riot-Token": api_key})
            rankinfo = json.loads(res.text)
            await ctx.send("소환사 이름: "+name)
            for i in rankinfo:
                if i["queueType"] == "RANKED_SOLO_5x5":
                    #솔랭과 자랭중 솔랭
                    await ctx.send("솔로랭크")
                    await ctx.send(f'티어: {i["tier"]} {i["rank"]}')
                    await ctx.send(f'승: {i["wins"]}판, 패: {i["losses"]}판')
                    await ctx.send(f'승률: {i["wins"]/(i["wins"]+i["losses"])*100:.2f}%')
                else:
                    # 솔랭과 자랭중 자랭
                    await ctx.send("자유랭크")
                    await ctx.send(f'티어: {i["tier"]} {i["rank"]}')
                    await ctx.send(f'승: {i["wins"]}판, 패: {i["losses"]}판')
                    await ctx.send(f'승률: {i["wins"]/(i["wins"]+i["losses"])*100:.2f}%')
        else:
            # 코드가 200이 아닐때(즉 찾는 닉네임이 없을때)
            await ctx.send("소환사가 존재하지 않습니다")


bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='wtf')
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('!도움말'))


@bot.event
async def on_message_delete(message):
    print(f"{message.content} 삭제됨")

@bot.event
async def on_message_edit(before, after):
    print(f"{before.content} 에서 {after.content} 로 편집됨.")

bot.add_cog(Music(bot))
bot.run('***REMOVED******REMOVED***')
