## 1. 라이브러리 설치

처음에 필요한 라이브러리들을 설치합니다. `beautifulsoup4`, `discord.py`, `yt_dlp` 등은 봇을 실행하는 데 필요한 패키지입니다. 패키지가 없다면 자동으로 설치하도록 되어 있습니다.

```python
package_list = ['beautifulsoup4','discord.py','discord.py[voice]','ffmpeg',
                'PyNaCl','requests','yt_dlp','html5lib']
```

## 2. API 키 로드

`api_keys.json` 파일에서 API 키를 읽어들입니다. 이 파일에는 Riot Games API와 Discord API 키가 포함되어야 합니다.

```python
with open('api_keys.json','r') as f:
    key = json.load(f)
riotKey = key['riot_key']
discordKey = key['discord_key']
betaKey = key['beta_key']
```

## 3. 유튜브 음악 재생 처리

`yt_dlp`를 사용하여 유튜브에서 음악을 다운로드하고 재생하는 기능을 구현하고 있습니다. 음악이 추가되면 대기열에 추가되고, 음성 채널에 연결하여 음악을 재생합니다.

### 대기열에 노래 추가

`/add` 명령어로 대기열에 노래를 추가하고, 대기열에 노래가 있을 경우 자동으로 플레이를 시작합니다.

```python
@bot.tree.command(name='add', description='대기열에 노래를 추가해요!')
async def add_music(interaction: discord.Interaction, title: str):
    ...
```

### 음악 재생

대기열에서 노래를 하나씩 빼서 재생합니다. 만약 음성 채널에서 노래가 재생 중이지 않다면, 대기열에서 노래를 하나 꺼내서 재생합니다.

```python
async def play_music(interaction: discord.Interaction):
    if not queue:
        embed = discord.Embed(title="대기중인 노래들이 없어요!", color=0x7AA600)
        await interaction.channel.send(embed=embed)
    else:
        title = queue.pop(0)
        player = await YTDLSource.from_url(title, loop=bot.loop, stream=True)
        interaction.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_music(interaction)))
```

## 4. 롤 관련 기능

`/tier`, `/most`, `/register` 등의 명령어로 롤 관련 정보를 제공할 수 있습니다.

### `/tier` 명령어

사용자의 롤 티어 정보를 가져와서 보여줍니다. Riot Games API를 사용하여 소환사의 티어 정보를 확인합니다.

```python
@bot.tree.command(name='tier', description='랭크 티어를 확인해요!')
async def reagueTier(interaction: discord.Interaction, nickname: str, tag: str):
    ...
```

### `/most` 명령어

사용자가 가장 많이 플레이한 챔피언을 보여줍니다.

```python
@bot.tree.command(name='most', description='모스트를 확인합니다')
async def reagueMost(interaction: discord.Interaction, nickname: str, tag: str):
    ...
```

## 5. 날씨 및 스팀 게임 가격 조회

`/weather` 명령어로 날씨를 조회하고, `/steam` 명령어로 스팀 게임의 가격을 확인할 수 있습니다.

### `/weather` 명령어

Naver 검색을 통해 입력한 위치의 날씨를 가져와서 보여줍니다.

```python
@bot.tree.command(name='weather', description='날씨를 확인해요!')
async def show_weather(interaction: discord.Interaction, location: str):
    ...
```

### `/steam` 명령어

스팀에서 게임을 검색하여 해당 게임의 가격을 확인할 수 있습니다.

```python
@bot.tree.command(name='steam', description='스팀에 있는 게임의 가격을 확인해요!')
async def steam_price(interaction: discord.Interaction, game: str):
    ...
```

## 6. 봇 실행

마지막으로 봇을 실행하는 부분입니다. `bot.run(betaKey)`에서 `betaKey`는 봇의 디스코드 토큰을 의미합니다.

```python
bot.run(betaKey)
```

## 주요 기능

* `/join`: 음성 채널에 연결
* `/quit`: 음성 채널에서 나가기
* `/add`: 대기열에 음악 추가
* `/queue`: 대기열 확인
* `/skip`: 음악 스킵
* `/pause`: 음악 일시정지/재개
* `/volume`: 볼륨 변경
* `/weather`: 날씨 확인
* `/steam`: 스팀 게임 가격 확인
* `/tier`: 롤 소환사 랭크 정보 확인
* `/most`: 롤 소환사의 모스트 챔피언 확인

## 실행

봇을 실행하려면 다음 명령어를 사용합니다:

```bash
python bot.py
```
