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
    from discord import app_commands
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
betaKey = key['beta_key']

verRes = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
lolVersion = verRes.json()

queue = [] # 노래 큐

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

class YTDLSource(discord.PCMVolumeTransformer): # 유튜브 오디오 소스 처리
    def __init__(self, source, *, data, volume=0.1):
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


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)


intents = discord.Intents.default()
intents.message_content = True
bot = MyClient(intents=intents)

@bot.event
async def on_ready(): # 봇이 시작 될 때
    await bot.tree.sync()
    print('sync')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Game('ㅎㅎ'))

@bot.event
async def on_message(message):# 서버에서 누군가 메세지를 보낼 때
     if message.author == bot.user: return # 봇이면 리턴
     if not message.content.startswith("/"): # 슬레쉬 커멘드가 아닐 때
          if (m := re.match(r"^<a?:[\w]+:([\d]+)>$", message.content)): # <a?(있어도 되고 없어도 됨):이름:아이디> 포멧이면
            if message.content.startswith("<a:"): # gif면
                ext = "gif"
            else:
                ext = "png"
            embed = discord.Embed(color=0x7AA600)
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{m.group(1)}.{ext}")
            await message.channel.send(embed=embed)
            await message.delete()

@bot.tree.command(name='join', description='음성 채널에 연결해요!')
async def join_channel(interaction: discord.Integration):
    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
            await interaction.response.send_message(embed=discord.Embed(description="연결했어요!", color=0x7AA600), ephemeral=True)
        else:
            embed = discord.Embed(title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed)

@bot.tree.command(name='quit', description='음성 채널에서 떠나요!')
async def quit_channel(interaction: discord.Integration):
    if interaction.guild.voice_client is None:
        embed = discord.Embed(title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message(embed=discord.Embed(description="나갔어요!", color=0x7AA600), ephemeral=True)

@bot.tree.command(name='add', description='대기열에 노래를 추가해요!')
async def add_music(interaction: discord.Integration, title: str):
    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
            await interaction.response.send_message(embed=discord.Embed(description="연결했어요!", color=0x7AA600), ephemeral=True)
        else:
            embed = discord.Embed(title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed)
            return    
    queue.append(title)
    await interaction.response.send_message(embed=discord.Embed(description="추가완료!", color=0x7AA600), ephemeral=True)
    if not interaction.guild.voice_client.is_playing():
        await play_music(interaction)

async def play_music(interaction: discord.Integration):
    if not queue:
        embed = discord.Embed(title="대기중인 노래들이 없어요!", description="/add 명령어로 노래를 추가해봐요!", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.channel.send(embed=embed)
    else:
        title = queue.pop(0)
        player = await YTDLSource.from_url(title, loop=bot.loop, stream=True)
        interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_music(interaction)))
        embed = discord.Embed(title=":musical_note: 지금 플레이 중인 노래!", description=player.title, color=0x7AA600)
        embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        await interaction.channel.send(embed=embed)

@bot.tree.command(name='queue', description='노래 대기열을 보여줘요!')
async def music_queue(interaction: discord.Integration):
    if queue:
        queue_list = ' :arrow_forward: '.join(queue)
        embed = discord.Embed(title="대기중인 노래들이에요!", description=queue_list, color=0x7AA600)
        embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="대기중인 노래들이 없어요!", description="/add 명령어로 노래를 추가해봐요!", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name='skip', description='노래를 스킵해요!')
async def skip_music(interaction: discord.Integration):
    if interaction.guild.voice_client is None:
        embed = discord.Embed(title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
    else:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message(embed=discord.Embed(description="스킵완료!", color=0x7AA600), ephemeral=True)

@bot.tree.command(name='pause', description='노래를 일시정지/재개해요!')
async def pause_music(interaction: discord.Integration):
    if interaction.guild.voice_client is None:
        embed = discord.Embed(title="채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
    else:
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message(embed=discord.Embed(description="일시정지 완료!", color=0x7AA600), ephemeral=True)
        else:
            interaction.guild.voice_client.resume()
            await interaction.response.send_message(embed=discord.Embed(description="재개 완료!", color=0x7AA600), ephemeral=True)

@bot.tree.command(name='volume', description='볼륨을 변경해요!')
async def volume_change(interaction: discord.Integration, volume: int):
    if volume < 0 or volume > 100:
        await interaction.response.send_message(embed=discord.Embed(description="볼륨은 0에서 100 사이여야 해요!", color=0x7AA600), ephemeral=True)
        return
    
    if interaction.guild.voice_client is None:
        embed = discord.Embed(title="음성 채널에 연결되지 않았어요!", description="ㅠㅠ", color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
    else:   
        interaction.guild.voice_client.source.volume = volume / 100
        await interaction.response.send_message(embed=discord.Embed(description=f"볼륨을 {volume}%로 바꿨어요!", color=0x7AA600))

@bot.tree.command(name='weather',description='날씨를 확인해요!')
async def show_weather(interaction: discord.Integration, location: str):
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
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='steam',description='스팀에 있는 게임의 가격을 확인해요!')
async def steam_price(interaction: discord.Integration,game: str):
    enc_game = urllib.parse.quote(game)
    steamUrl = 'https://store.steampowered.com/search/?l=koreana&term=' + enc_game
    req = Request(steamUrl)
    page = urlopen(req)
    html = page.read()
    soup = bs4.BeautifulSoup(html, 'html5lib')
    if soup.find('span', class_='title') is not None:
        await interaction.response.send_message(embed=discord.Embed(title=f"{game}의 검색결과", color=0x7AA600))
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
            await interaction.followup.send(embed=embed)
            if i >= 2:
                break

async def reaguePuuid(nickname: str, tag: str): # 닉네임과 테그로 puuid를 불러오는 함수
    URL = "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"+nickname+'/'+tag
    res = requests.get(URL, headers={"X-Riot-Token": riotKey})
    if res.status_code == 200:
        data = res.json()
        return data["puuid"]

@bot.tree.command(name='tier',description='랭크 티어를 확인해요!')
async def reagueTier(interaction: discord.Integration, nickname: str,tag: str):
    if (nickname,tag) is not None:
        puuid = await reaguePuuid(nickname,tag)
        URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/"+puuid
        res = requests.get(URL, headers={"X-Riot-Token": riotKey})
        if res.status_code == 200:
            data=res.json()
            embed = discord.Embed(title=f'랭크 전적!',
                                  description=f'{nickname} 의 전적을\n불러오고 있어요!',
                                  color=0x7AA600)
            embed.set_thumbnail(url="http://ddragon.leagueoflegends.com/cdn/"+ f'{lolVersion[0]}' +"/img/profileicon/"+f'{data["profileIconId"]}'+'.png')
            await interaction.response.send_message(embed=embed)
            URL = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/" + f'{data["id"]}'
            rankinfo = requests.get(URL, headers={"X-Riot-Token": riotKey})
            rankData = rankinfo.json()
            def prntTier(tier,isSolo):
                if isSolo == True:
                    Rank="솔로랭크"
                else:
                    Rank="자유랭크"
                embed = discord.Embed(title=Rank,
                                      description=f' :trophy:  : {i["tier"]} {i["rank"]}\n'
                                                  f' :v:  : {i["wins"]} :poop:  : {i["losses"]}\n'
                                                  f' :dart:  : {i["wins"] / (i["wins"] + i["losses"]) * 100:.2f}%',
                                      color=0x7AA600)
                if tier == 1: # 아이언
                    embed.set_thumbnail(url="https://i.imgur.com/jMCF0jp.png")
                elif tier == 2: # 브론즈
                    embed.set_thumbnail(url="https://i.imgur.com/Yr5zIKg.png")
                elif tier == 3: # 실버
                    embed.set_thumbnail(url="https://i.imgur.com/ydwcOgT.png")
                elif tier == 4: # 골드
                    embed.set_thumbnail(url="https://i.imgur.com/Qpmwjxg.png")
                elif tier == 5: # 에메랄드
                    embed.set_thumbnail(url="https://i.imgur.com/JIkmK7x.png")
                elif tier == 6: # 플레티넘
                    embed.set_thumbnail(url="https://i.imgur.com/IhnXzoB.png")
                elif tier == 7: # 다이아
                    embed.set_thumbnail(url="https://i.imgur.com/1uYnavY.png")
                elif tier == 8: # 마스터
                    embed.set_thumbnail(url="https://i.imgur.com/ScVNf2g.png")
                elif tier == 9: # 그랜드마스터
                    embed.set_thumbnail(url="https://i.imgur.com/TyASwqZ.png")
                elif tier == 10: # 첼린저
                    embed.set_thumbnail(url="https://i.imgur.com/Zfvk2BJ.png")
                return embed
            for i in rankData:
                if i["queueType"] == "RANKED_SOLO_5x5":
                    # 솔랭과 자랭중 솔랭
                    if i["tier"] == "IRON":
                        await interaction.followup.send(embed=prntTier(1, True))
                    if i["tier"] == "BRONZE":
                        await interaction.followup.send(embed=prntTier(2, True))
                    if i["tier"] == "SILVER":
                        await interaction.followup.send(embed=prntTier(3, True))
                    if i["tier"] == "GOLD":
                        await interaction.followup.send(embed=prntTier(4, True))
                    if i["tier"] == "EMERALD":
                        await interaction.followup.send(embed=prntTier(5, True))
                    if i["tier"] == "PLATINUM":
                        await interaction.followup.send(embed=prntTier(6, True))
                    if i["tier"] == "DIAMOND":
                        await interaction.followup.send(embed=prntTier(7, True))
                    if i["tier"] == "MASTER":
                        await interaction.followup.send(embed=prntTier(8, True))
                    if i["tier"] == "GRANDMASTER":
                        await interaction.followup.send(embed=prntTier(9, True))
                    if i["tier"] == "CHALLENGER":
                        await interaction.followup.send(embed=prntTier(10, True))
                elif i["queueType"] == "RANKED_FLEX_SR":
                    # 솔랭과 자랭중 자랭
                    if i["tier"] == "IRON":
                        await interaction.followup.send(embed=prntTier(1, False))
                    if i["tier"] == "BRONZE":
                        await interaction.followup.send(embed=prntTier(2, False))
                    if i["tier"] == "SILVER":
                        await interaction.followup.send(embed=prntTier(3, False))
                    if i["tier"] == "GOLD":
                        await interaction.followup.send(embed=prntTier(4, False))
                    if i["tier"] == "EMERALD":
                        await interaction.followup.send(embed=prntTier(5, True))
                    if i["tier"] == "PLATINUM":
                        await interaction.followup.send(embed=prntTier(6, False))
                    if i["tier"] == "DIAMOND":
                        await interaction.followup.send(embed=prntTier(7, False))
                    if i["tier"] == "MASTER":
                        await interaction.followup.send(embed=prntTier(8, False))
                    if i["tier"] == "GRANDMASTER":
                        await interaction.followup.send(embed=prntTier(9, False))
                    if i["tier"] == "CHALLENGER":
                        await interaction.followup.send(embed=prntTier(10, False))
        else:
            embed=discord.Embed(title="등록 하셨나요?",
                                description="/register [등록될 이름] [롤닉] [태그]로 등록 가능해요!",
                                color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed)
    else:
        embed=discord.Embed(title="등록된 이름을 정확히 입력해주세요!",
                            description="/register [등록될 이름] [롤닉] [태그]로 등록 가능해요!",
                            color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name='most',description='모스트를 확인합니다')
async def reagueMost(interaction: discord.Integration, nickname: str,tag: str):
    if (nickname,tag) is not None:
        
        puuid = await reaguePuuid(nickname,tag)
        URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/"+puuid
        res = requests.get(URL, headers={"X-Riot-Token": riotKey})
        if res.status_code == 200:
            URL = "https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/" + puuid
            res = requests.get(URL, headers={"X-Riot-Token": riotKey})
            mostInfo=res.json()
            j=0
            await interaction.response.send_message(embed=discord.Embed(title=f'{nickname}의 모스트',color=0x7AA600))
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
                await interaction.followup.send(embed=embed)
                j += 1
                if j >= 3:
                    break
        else:
            embed = discord.Embed(title="등록을 했나요?",
                                  description="/register [등록될 이름] [롤닉] [태그]로 등록 가능합니다!",
                                  color=0x7AA600)
            embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="등록된 이름을 입력해주세요!",
                              description="등록을 안했다면 /register [등록될 이름] [롤닉] [태그]로 등록 가능합니다!\nex)/most [등록한 이름]",
                              color=0x7AA600)
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
        await interaction.response.send_message(embed=embed)
        
bot.run(betaKey) # 서버 : discordKey / 테스트 : betaKey

