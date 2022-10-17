 #-*- coding:utf-8 -*-
import asyncio
import discord
import youtube_dl
from neispy import Neispy
import json
import requests
from urllib.request import urlopen, Request
import urllib
import bs4
import re
import logging
from discord.ext import commands


name="울산애니원고등학교" # 급식 학교 이름
api_key = "***REMOVED***" # 라이엇 api 키
neis = Neispy.sync('***REMOVED***') # 네이스 api 키
scinfo = neis.schoolInfo(SCHUL_NM=name)
AE = scinfo[0].ATPT_OFCDC_SC_CODE  # 교육청코드
SE = scinfo[0].SD_SCHUL_CODE  # 학교코드
reqVersion=requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
loadJson=reqVersion.json()
lolVersion=loadJson[0]


try:
    scmeal = neis.mealServiceDietInfo(AE, SE)# MLSV_YMD=datetime.today().strftime("%Y%m%d")
    meal1 = scmeal[0].DDISH_NM.replace("<br/>", "\n")
    meal2 = scmeal[1].DDISH_NM.replace("<br/>", "\n")
    meal3 = scmeal[2].DDISH_NM.replace("<br/>", "\n")
except Exception as e:
    meal1 = '급식이 없어요!'
    meal2 = '급식이 없어요!'
    meal3 = '급식이 없어요!'


youtube_dl.utils.bug_report_message = lambda: ''

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


class Command(commands.Cog):
    def __init__(self,bot):
        self.bot=bot

    @commands.command()
    async def 도움말(self, ctx):
        embed=discord.Embed(title="명령어 앞에는 느낌표!",
                            description="들어와\n"
                                        "나가\n"
                                        "노래 [노래제목]\n"
                                        "볼륨 [0~100]\n"
                                        "멈춰\n"
                                        "아침\n"
                                        "점심\n"
                                        "저녘\n"
                                        "롤전적 [닉넴]\n"
                                        "모스트 [닉넴]\n"
                                        "날씨 [지역]\n"
                                        "스팀 [게임이름]",
                            color=0x7AA600)
        embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        await ctx.send(embed=embed)

    
    @commands.command()
    async def 들어와(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed=discord.Embed(title="당신은 음성 채널에 연결되있지 않아요!",
                                    description="ㅠㅠ",
                                    color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)

    @commands.command()
    async def 노래(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'에러 : {e}') if e else None)

        await ctx.send(embed=discord.Embed(description=f':play_pause: 지금 플레이 중인 노래 : {player.title}',
                                           color=0x7AA600))

    @commands.command()
    async def 볼륨(self, ctx, volume: int):
        if ctx.voice_client is None:
            embed=discord.Embed(title="음성 채널에 연결되있지 않아요!",
                                description="ㅠㅠ",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)
        else:   
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(embed=discord.Embed(description=f"볼륨을 {volume}%로 바꿨어요!",
                                               color=0x7AA600))

    @commands.command()
    async def 나가(self, ctx):
        if ctx.voice_client is None:
            embed=discord.Embed(title="음성 채널에 연결되있지 않아요!",
                                description="ㅠㅠ",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)
        else:
            await ctx.voice_client.disconnect()

    @commands.command()
    async def 멈춰(self, ctx):
        if ctx.voice_client is None:
            embed=discord.Embed(title="음성 채널에 연결되있지 않아요!",
                                description="ㅠㅠ",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)
        else:
            ctx.voice_client.stop()

    @노래.before_invoke
    async def ensure_voice(self, ctx):#노래 자동으로 와서 틀기
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed=discord.Embed(title="당신은 음성 채널에 연결되있지 않아요!",
                                    description="ㅠㅠ",
                                    color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            
    @commands.command()
    async def 아침(self, ctx):
        await ctx.send(embed=discord.Embed(description=f"{meal1}",
                                           color=0x7AA600))
        
    @commands.command()
    async def 점심(self, ctx):
        await ctx.send(embed=discord.Embed(description=f"{meal2}",
                                           color=0x7AA600))
        
    @commands.command()
    async def 저녘(self, ctx):
        await ctx.send(embed=discord.Embed(description=f"{meal3}",
                                           color=0x7AA600))

    @commands.command()
    async def 청소(self, ctx, amount : int):
        if ctx.author.id == 315462084710367233:
            await ctx.channel.purge(limit=amount+1)
            embed = discord.Embed(title=f'{amount}개의 메세지가 삭제되었어요!',
                                description="이 메세지는 3초후 폭파되요!",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
            boom = await ctx.send(" https://tenor.com/view/exploding-boom-explosion-mind-blowing-gif-10728578 ")
            await asyncio.sleep(1)
            await boom.delete()
        else:
            embed=discord.Embed(description="ㅠㅠ",color=0x7AA600)
            embed.set_author(name="당신은 어드민이 아니에요!")
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)

    @commands.command()
    async def 날씨(self, ctx, *,location):
        enc_location = urllib.parse.quote(location + '+날씨')
        TempUrl = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=' + enc_location
        req = Request(TempUrl)
        page = urlopen(req)
        html = page.read()
        soup=bs4.BeautifulSoup(html,'html5lib')
        tempInfo = soup.find('p', class_='summary').text.split()
        embed = discord.Embed(title=soup.find('div', class_='temperature_text').text ,
                              description = tempInfo[0]+tempInfo[1]+tempInfo[2]+'!\n'+f'날씨는 "{tempInfo[3]}"!\n'
                              + f'체감 온도는 ' + soup.find_all('dd', class_='desc')[0].text + '!\n'
                              + f'습도는  ' + soup.find_all('dd', class_='desc')[1].text + '!\n'
                              + f'풍속은 ' + soup.find_all('dd', class_='desc')[2].text + '!\n' ,
                              color=0x7AA600)
        embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def 스팀(self, ctx, *,game):
        enc_game = urllib.parse.quote(game)
        steamUrl = 'https://store.steampowered.com/search/?l=koreana&term=' + enc_game
        req = Request(steamUrl)
        page = urlopen(req)
        html = page.read()
        soup = bs4.BeautifulSoup(html, 'html5lib')
        if soup.find('span', class_='title') is not None:
            for i in range(0, len(soup.find_all('span', class_='title'))):
                embed = discord.Embed()
                price = soup.find_all('div', class_='col search_price_discount_combined responsive_secondrow')[i].text
                price1 = re.sub('₩', '', price)
                if len(price1.split()) == 3:
                    embed = discord.Embed(title = soup.find_all('span', class_='title')[i].text ,
                                          description = price1.split()[0] + '세일해서 ' + price1.split()[1] + '->' + price1.split()[2]+' 입니다!',
                                          color=0x7AA600)
                else:
                    embed = discord.Embed(title = soup.find_all('span', class_='title')[i].text,
                                          description = price1.split()[0] + ' 입니다!',
                                          color=0x7AA600)
                await ctx.send(embed=embed)
                if i >= 2:
                    break

    @commands.command()
    async def 롤전적(self, ctx, *, name = None):
        if name is not None:
            URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/"+name
            res = requests.get(URL, headers={"X-Riot-Token": api_key})
            if res.status_code == 200:
                # 코드가 200일때
                resobj = json.loads(res.text)
                embed = discord.Embed(title=f'랭크 전적!',
                                      description=f'{name} 님의 전적을\n불러오고 있어요!',
                                      color=0x7AA600)
                icon=f'{resobj["profileIconId"]}'
                embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/"+ lolVersion +"/img/profileicon/"+icon+'.png')
                await ctx.send(embed=embed)
                URL = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/"+resobj["id"]
                res = requests.get(URL, headers={"X-Riot-Token": api_key})
                rankinfo = json.loads(res.text)

                def prntTier(tier,isSolo):
                    if isSolo == True:
                        Rank="솔로랭크"
                    else:
                        Rank="자유랭크"
                    embed = discord.Embed(title=Rank,
                                          description=f'티어: {i["tier"]} {i["rank"]}\n'
                                                      f'승: {i["wins"]}판, 패: {i["losses"]}판\n'
                                                      f'승률: {i["wins"] / (i["wins"] + i["losses"]) * 100:.2f}%',
                                          color=0x7AA600)
                    if tier == 1:
                        embed.set_thumbnail(url="https://i.imgur.com/a9Kpj7y.png")
                    elif tier == 2:
                        embed.set_thumbnail(url="https://i.imgur.com/umLjHzW.png")
                    elif tier == 3:
                        embed.set_thumbnail(url="https://i.imgur.com/4igsYZO.png")
                    elif tier == 4:
                        embed.set_thumbnail(url="https://i.imgur.com/hCHuKhg.png")
                    elif tier == 5:
                        embed.set_thumbnail(url="https://i.imgur.com/r5TcH3l.png")
                    elif tier == 6:
                        embed.set_thumbnail(url="https://i.imgur.com/FKYMP3D.png")
                    elif tier == 7:
                        embed.set_thumbnail(url="https://i.imgur.com/dJG4Gbr.png")
                    elif tier == 8:
                        embed.set_thumbnail(url="https://i.imgur.com/5g5bTD9.png")
                    elif tier == 9:
                        embed.set_thumbnail(url="https://i.imgur.com/qk9H0FE.png")
                    return embed

                for i in rankinfo:
                    if i["queueType"] == "RANKED_SOLO_5x5":
                        # 솔랭과 자랭중 솔랭
                        if i["tier"] == "IRON":
                            await ctx.send(embed=prntTier(1, True))
                        if i["tier"] == "BRONZE":
                            await ctx.send(embed=prntTier(2, True))
                        if i["tier"] == "SILVER":
                            await ctx.send(embed=prntTier(3, True))
                        if i["tier"] == "GOLD":
                            await ctx.send(embed=prntTier(4, True))
                        if i["tier"] == "PLATINUM":
                            await ctx.send(embed=prntTier(5, True))
                        if i["tier"] == "DIAMOND":
                            await ctx.send(embed=prntTier(6, True))
                        if i["tier"] == "MASTER":
                            await ctx.send(embed=prntTier(7, True))
                        if i["tier"] == "GRANDMASTER":
                            await ctx.send(embed=prntTier(8, True))
                        if i["tier"] == "CHALLENGER":
                            await ctx.send(embed=prntTier(9, True))
                    else:
                        # 솔랭과 자랭중 자랭
                        if i["tier"] == "IRON":
                            await ctx.send(embed=prntTier(1, False))
                        if i["tier"] == "BRONZE":
                            await ctx.send(embed=prntTier(2, False))
                        if i["tier"] == "SILVER":
                            await ctx.send(embed=prntTier(3, False))
                        if i["tier"] == "GOLD":
                            await ctx.send(embed=prntTier(4, False))
                        if i["tier"] == "PLATINUM":
                            await ctx.send(embed=prntTier(5, False))
                        if i["tier"] == "DIAMOND":
                            await ctx.send(embed=prntTier(6, False))
                        if i["tier"] == "MASTER":
                            await ctx.send(embed=prntTier(7, False))
                        if i["tier"] == "GRANDMASTER":
                            await ctx.send(embed=prntTier(8, False))
                        if i["tier"] == "CHALLENGER":
                            await ctx.send(embed=prntTier(9, False))
            else:
                embed=discord.Embed(title="소환사가 존재하지 않아요!",
                                    description="ㅠㅠ",
                                    color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title="소환사 닉네임을 입력해주세요!",
                                description="ex) !롤전적 고기냠냠먹음",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)

    @commands.command()
    async def 모스트(self, ctx, *, name = None):
        if name is not None:
            URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name
            res = requests.get(URL, headers={"X-Riot-Token": api_key})
            if res.status_code == 200:
                resobj = json.loads(res.text)
                URL = "https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/" + resobj["id"]
                res = requests.get(URL, headers={"X-Riot-Token": api_key})
                mostInfo=json.loads(res.text)
                j=0
                for i in mostInfo:
                    req = requests.get("http://ddragon.leagueoflegends.com/cdn/"+ lolVersion +"/data/ko_KR/champion.json")
                    loadJson = req.json()
                    data = loadJson['data']
                    d = {v['key']: h for h, v in data.items()}
                    mostName = data[d[f'{i["championId"]}']]['name']
                    mostLevel = i["championLevel"]
                    mostPoints = i["championPoints"]
                    img = data[d[f'{i["championId"]}']]['image']['full']
                    embed = discord.Embed(title=f'모스트{j+1}은(는) {mostName}에요!',
                                          description=f'{mostLevel}레벨\n{mostPoints} 포인트',
                                          color=0x7AA600)
                    embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/"+ lolVersion +"/img/champion/"+img)
                    await ctx.send(embed=embed)
                    j += 1
                    if j >= 3:
                        break
            else:
                embed = discord.Embed(title="소환사가 존재하지 않아요!",
                                      description="ㅠㅠ",
                                      color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="소환사 닉네임을 입력해주세요!",
                                  description="ex) !모스트 고기냠냠먹음",
                                  color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='music bot',
    intents=intents,
)


@bot.event
async def on_message(message):
    if (m := re.match(r"^<a?:[\w]+:([\d]+)>$", message.content)):
        if message.content.startswith("<a:"):
            ext = "gif"
        else:
            ext = "png"
        embed = discord.Embed(color=0x7AA600)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.set_image(url=f"https://cdn.discordapp.com/emojis/{m.group(1)}.{ext}")
        await message.channel.send(embed=embed)
        await message.delete()
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Game('!도움말'))

@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed(description=f'명령어가 없거나 걍 오류에요!\n'
                                    f'"!도움말"로 명령어를 알아보세요!',
                        color=0x7AA600)
    embed.set_author(name="Error!!")
    embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
    logging.error(error)
    await ctx.send(embed=embed)

async def main():
    async with bot:
        await bot.add_cog(Command(bot))
        await bot.start('***REMOVED***')

asyncio.run(main())
