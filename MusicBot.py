 #-*- coding:utf-8 -*-

package_list = ['beautifulsoup4','discord.py','discord.py[voice]','ffmpeg',
                'PyNaCl','requests','yt_dlp','html5lib']
try:
    import asyncio
    import discord
    import yt_dlp   
    import json
    import requests
    from urllib.request import urlopen, Request
    import urllib
    import bs4
    import re
    import logging
    from discord.ext import commands
except:
    import sys
    import subprocess
    for package in package_list:
        subprocess.check_call([sys.executable,'-m','pip','install','-U',package])
        print(package+' 완료')

try:
    with open('api_keys.json','r') as f:
                key = json.load(f)
except:
    with open('api_keys.json','r') as f:
                key = json.load(f)
riotKey = key['riot_key']
discordKey = key['discord_key']

verRes = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
lolVersion = verRes.json()

yt_dlp.utils.bug_report_message = lambda: ''

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
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

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

    @commands.command(name='comhelp',aliases=['도움말'],description='명령어를 보여줍니다')
    async def comhelp(self, ctx):
        embed=discord.Embed(title="명령어 앞에는 느낌표!",
                            description="들어와 / 들어가기 / 참여\n"
                                        "나가 / 나가 / 퇴장\n"
                                        "노래 / 유튜브 / 음악 [노래제목]\n"
                                        "볼륨 / 소리 [0~100]\n"
                                        "멈춰 / 중지 / 끄기\n"
                                        "등록 [등록할 이름] [닉넴] [태그]\n"
                                        "랭크 / 티어 [등록된 이름]\n"
                                        "모스트 [등록된 이름]\n"
                                        "날씨 [지역]\n"
                                        "스팀 / 게임 [게임이름]",
                            color=0x7AA600)
        embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        await ctx.send(embed=embed)

    
    @commands.command(name='join',aliases=['들어와','들어가기','참여'],description='당신의 음성 채널에 연결합니다')
    async def join(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed=discord.Embed(title="당신은 음성 채널에 연결되있지 않아요!",
                                    description="ㅠㅠ",
                                    color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)

    @commands.command(name='song',aliases=['노래','유튜브','음악'],description='노래를 틉니다')
    async def song(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'에러 : {e}') if e else None)

        await ctx.send(embed=discord.Embed(description=f':play_pause: 지금 플레이 중인 노래 : {player.title}',
                                           color=0x7AA600))

    @commands.command(name='volume',aliases=['볼륨','소리'],description='볼륨을 변경합니다')
    async def volume(self, ctx, volume: int):
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

    @commands.command(name='quit',aliases=['나가','퇴장'],description='당신의 음성 채널에서 나갑니다')
    async def quit(self, ctx):
        if ctx.voice_client is None:
            embed=discord.Embed(title="음성 채널에 연결되있지 않아요!",
                                description="ㅠㅠ",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)
        else:
            await ctx.voice_client.disconnect()

    @commands.command(name='stop',aliases=['멈춰','중지','끄기'],description='노래를 정지합니다')
    async def stop(self, ctx):
        if ctx.voice_client is None:
            embed=discord.Embed(title="음성 채널에 연결되있지 않아요!",
                                description="ㅠㅠ",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)
        else:
            ctx.voice_client.stop()

    @song.before_invoke
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

    @commands.command(name='clean',aliases=['청소','지우기'],description='메세지를 삭제합니다',hidden=True)
    async def clean(self, ctx, amount : int):
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

    @commands.command(name='weather',aliases=['날씨'],description='날씨를 확인합니다')
    async def weather(self, ctx, *,location):
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

    @commands.command(name='steam',aliases=['스팀','게임'],description='스팀에 있는 게임의 가격을 확인합니다')
    async def steam(self, ctx, *,game):
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

    @commands.command(name='reagueRegitrion',aliases=['등록'],description='롤 아이디를 데이터베이스에 등록합니다')
    async def reagueRegistrion(self, ctx, text, name, tag):
        URL = "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"+name+'/'+tag
        res = requests.get(URL, headers={"X-Riot-Token": riotKey})
        if res.status_code == 200:
            data = res.json()
            obj={
                ctx.author.id:{
                    text : data["puuid"]
                }
            }
            with open('reagueData.json','w') as f:
                json.dump(obj,f,indent=2)


    @commands.command(name='reagueTier',aliases=['랭크','티어'],description='랭크 티어를 확인합니다')
    async def reagueTier(self, ctx, *, name):
        if name is not None:
            with open('reagueData.json','r') as f:
                playerData = json.load(f)
            puuidtemp = playerData[f'{ctx.author.id}']
            puuid = puuidtemp[f'{name}']
            URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/"+puuid
            res = requests.get(URL, headers={"X-Riot-Token": riotKey})
            if res.status_code == 200:
                data=res.json()
                embed = discord.Embed(title=f'랭크 전적!',
                                      description=f'{ctx.author.name} 님의 전적을\n불러오고 있어요!',
                                      color=0x7AA600)
                embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/"+ f'{lolVersion[0]}' +"/img/profileicon/"+f'{data["profileIconId"]}'+'.png')
                await ctx.send(embed=embed)
                URL = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/" + f'{data["id"]}'
                rankinfo = requests.get(URL, headers={"X-Riot-Token": riotKey})
                rankData = rankinfo.json()
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

                for i in rankData:
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
                    elif i["queueType"] == "RANKED_FLEX_SR":
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
                embed=discord.Embed(title="등록 하셨나요?",
                                    description="!등록 [등록될 이름] [롤닉] [태그]로 등록 가능합니다!",
                                    color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title="등록된 이름을 정확히 입력해주세요!",
                                description="!등록 [등록될 이름] [롤닉] [태그]로 등록 가능합니다!",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await ctx.send(embed=embed)

    @commands.command(name='reagueMost',aliases=['모스트'],description='모스트를 확인합니다')
    async def reagueMost(self, ctx, *, name = None):
        if name is not None:
            with open('reagueData.json','r') as f:
                playerData = json.load(f)
            puuidtemp = playerData[f'{ctx.author.id}']
            puuid = puuidtemp[f'{name}']
            URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/"+puuid
            res = requests.get(URL, headers={"X-Riot-Token": riotKey})
            if res.status_code == 200:
                resobj = res.json()
                URL = "https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/" + puuid
                res = requests.get(URL, headers={"X-Riot-Token": riotKey})
                mostInfo=res.json()
                j=0
                for i in mostInfo:
                    req = requests.get("http://ddragon.leagueoflegends.com/cdn/"+ f'{lolVersion[0]}' +"/data/ko_KR/champion.json")
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
                    embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/"+ f'{lolVersion[0]}' +"/img/champion/"+img)
                    await ctx.send(embed=embed)
                    j += 1
                    if j >= 3:
                        break
            else:
                embed = discord.Embed(title="등록을 했나요?",
                                      description="!등록 [등록될 이름] [롤닉] [태그]로 등록 가능합니다!",
                                      color=0x7AA600)
                embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="등록된 이름을 입력해주세요!",
                                  description="등록을 안했다면 !등록 [등록될 이름] [롤닉] [태그]로 등록 가능합니다!\nex)!모스트 본계",
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
        await bot.start(discordKey)

asyncio.run(main())
