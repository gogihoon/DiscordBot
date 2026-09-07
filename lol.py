import asyncio
import logging
import time
import urllib.parse

import discord
import requests

from config import RIOT_KEY
from utils import Responder, crash_embed, error_embed

log = logging.getLogger(__name__)

DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
# ddragon에서 한 번도 못 받았을 때 쓸 기본값
FALLBACK_VERSION = "16.17.1"
VERSION_TTL = 6 * 60 * 60  # 6시간마다 최신 버전을 다시 확인한다
VERSION_RETRY = 5 * 60  # 실패했을 땐 5분 뒤에 다시 시도한다

_version = FALLBACK_VERSION
_next_version_check = 0.0  # time.monotonic() 기준, 이 시각이 지나면 다시 확인한다
_version_lock = asyncio.Lock()


async def get_lol_version():
    """ddragon 최신 버전을 주기적으로 갱신해서 돌려준다.

    봇을 켤 때 한 번만 읽으면 패치가 나온 뒤로 이미지 주소가 전부 404가 되므로
    일정 시간마다 다시 받는다. 갱신에 실패하면 마지막으로 성공한 값을 그대로 쓴다.
    """
    global _version, _next_version_check

    if time.monotonic() < _next_version_check:
        return _version

    async with _version_lock:
        # 락을 기다리는 사이 다른 명령이 이미 갱신했을 수 있다.
        now = time.monotonic()
        if now < _next_version_check:
            return _version
        try:
            res = await asyncio.to_thread(
                requests.get, DDRAGON_VERSIONS_URL, timeout=10
            )
            versions = res.json() if res.status_code == 200 else None
        except (requests.RequestException, ValueError) as e:
            log.warning("버전 갱신 실패, %s 을(를) 유지해요: %s", _version, e)
            _next_version_check = now + VERSION_RETRY
            return _version

        if isinstance(versions, list) and versions:
            if versions[0] != _version:
                log.info("롤 버전을 %s -> %s 로 갱신했어요.", _version, versions[0])
            _version = versions[0]
            _next_version_check = now + VERSION_TTL
        else:
            log.warning("버전 목록이 비어 있어 %s 을(를) 유지해요.", _version)
            _next_version_check = now + VERSION_RETRY
    return _version


TIER_IMG = {
    "IRON": "https://i.imgur.com/jMCF0jp.png",
    "BRONZE": "https://i.imgur.com/Yr5zIKg.png",
    "SILVER": "https://i.imgur.com/ydwcOgT.png",
    "GOLD": "https://i.imgur.com/Qpmwjxg.png",
    "PLATINUM": "https://i.imgur.com/JIkmK7x.png",
    "EMERALD": "https://i.imgur.com/IhnXzoB.png",
    "DIAMOND": "https://i.imgur.com/1uYnavY.png",
    "MASTER": "https://i.imgur.com/ScVNf2g.png",
    "GRANDMASTER": "https://i.imgur.com/TyASwqZ.png",
    "CHALLENGER": "https://i.imgur.com/Zfvk2BJ.png",
}


def setup_lol_commands(bot):
    async def api_get(url: str, *, auth: bool = True):
        """requests가 이벤트 루프를 막지 않도록 별도 스레드에서 호출한다."""
        headers = {"X-Riot-Token": RIOT_KEY} if auth else {}
        return await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)

    async def riot_get_puuid(nickname: str, tag: str):
        URL = (
            "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
            f"{urllib.parse.quote(nickname)}/{urllib.parse.quote(tag)}"
        )
        try:
            res = await api_get(URL)
        except requests.RequestException:
            return None
        if res.status_code != 200:
            return None
        return res.json().get("puuid")

    async def get_profile_icon(puuid: str):
        """소환사 프로필 아이콘 주소를 가져온다. 실패하면 None."""
        URL = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        res = await api_get(URL)
        if res.status_code != 200:
            return None
        icon_id = res.json().get("profileIconId")
        if icon_id is None:
            return None
        version = await get_lol_version()
        return f"http://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{icon_id}.png"

    @bot.tree.command(name="tier", description="롤 랭크 티어를 확인해요!")
    async def league_tier(interaction: discord.Interaction, nickname: str, tag: str):
        # 결과를 채널에 공개로 남긴다. 라이엇 API가 3초를 넘길 수 있어 먼저 응답을 유예한다.
        await interaction.response.defer()
        reply = Responder(interaction)
        try:
            puuid = await riot_get_puuid(nickname, tag)
            if not puuid:
                await reply.send(error_embed("닉네임과 태그를 정확히 입력해주세요!"))
                return

            # 프로필 아이콘은 장식이라 못 가져와도 티어 조회는 그대로 진행한다.
            icon_url = await get_profile_icon(puuid)
            summoner = f"{nickname} #{tag}"

            embed = discord.Embed(
                title="랭크 전적!",
                description=f"{summoner} 의 전적을\n불러오고 있어요!",
                color=0x7AA600,
            )
            if icon_url:
                embed.set_thumbnail(url=icon_url)
            await reply.send(embed)

            URL = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
            rankinfo = await api_get(URL)
            rankData = rankinfo.json() if rankinfo.status_code == 200 else None
            if not isinstance(rankData, list):
                # 키 만료(403)나 호출 제한(429)이면 응답이 리스트가 아닌 오류 dict로 온다.
                await reply.send(
                    error_embed(
                        "랭크 정보를 불러오지 못했어요.",
                        f"(라이엇 API 응답 코드 : {rankinfo.status_code})",
                    )
                )
                return

            found = False
            for i in rankData:
                if i.get("queueType") not in ("RANKED_SOLO_5x5", "RANKED_FLEX_SR"):
                    continue
                found = True
                qtype = (
                    "솔로랭크" if i["queueType"] == "RANKED_SOLO_5x5" else "자유랭크"
                )
                wins = i.get("wins", 0)
                losses = i.get("losses", 0)
                total = wins + losses
                winrate = f"{wins / total * 100:.2f}%" if total else "기록 없음"
                embed = discord.Embed(
                    title=qtype,
                    description=f' :trophy:  : {i.get("tier", "?")} {i.get("rank", "")}\n'
                    f" :v:  : {wins} :poop:  : {losses}\n"
                    f" :dart:  : {winrate}",
                    color=0x7AA600,
                )
                # 메시지가 여러 개로 나뉘어도 누구 전적인지 보이도록 닉네임을 붙인다.
                embed.set_author(name=summoner, icon_url=icon_url or "")
                embed.set_thumbnail(url=TIER_IMG.get(i.get("tier"), ""))
                await reply.send(embed)

            if not found:
                await reply.send(
                    error_embed(
                        f"{summoner} 는 아직 랭크 전적이 없어요!",
                        "솔로랭크나 자유랭크를 플레이해봐요!",
                    )
                )
        except Exception as e:
            await reply.send(crash_embed(f"티어 정보를 불러오는 중 오류: {str(e)}"))

    @bot.tree.command(name="most", description="롤 모스트 챔피언을 확인해요!")
    async def league_most(interaction: discord.Interaction, nickname: str, tag: str):
        # 결과를 채널에 공개로 남긴다.
        await interaction.response.defer()
        reply = Responder(interaction)
        try:
            puuid = await riot_get_puuid(nickname, tag)
            if not puuid:
                await reply.send(error_embed("닉네임과 태그를 정확히 입력해주세요!"))
                return

            summoner = f"{nickname} #{tag}"
            URL = f"https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
            res = await api_get(URL)
            mostInfo = res.json() if res.status_code == 200 else None
            if not isinstance(mostInfo, list):
                await reply.send(
                    error_embed(
                        "모스트 정보를 불러오지 못했어요.",
                        f"(라이엇 API 응답 코드 : {res.status_code})",
                    )
                )
                return
            if not mostInfo:
                await reply.send(
                    error_embed(
                        f"{summoner} 는 숙련도 정보가 없어요!", "게임을 한 판 해봐요!"
                    )
                )
                return

            icon_url = await get_profile_icon(puuid)
            header = discord.Embed(title=f"{summoner} 의 모스트", color=0x7AA600)
            if icon_url:
                header.set_thumbnail(url=icon_url)
            await reply.send(header)

            version = await get_lol_version()
            req = await api_get(
                f"http://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion.json",
                auth=False,
            )
            champ_data = req.json()["data"]
            key_to_name = {v["key"]: k for k, v in champ_data.items()}
            for j, i in enumerate(mostInfo[:3]):
                champ = champ_data.get(key_to_name.get(str(i["championId"]), ""))
                if champ is None:
                    # 신규 챔피언이라 버전 데이터에 아직 없는 경우
                    continue
                embed = discord.Embed(
                    title=f"모스트{j + 1}은(는) {champ['name']}에요!",
                    description=f"{i['championLevel']}레벨\n{i['championPoints']} 포인트",
                    color=0x7AA600,
                )
                # 메시지가 여러 개로 나뉘어도 누구 모스트인지 보이도록 닉네임을 붙인다.
                embed.set_author(name=summoner, icon_url=icon_url or "")
                embed.set_thumbnail(
                    url=f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ['image']['full']}"
                )
                await reply.send(embed)
        except Exception as e:
            await reply.send(crash_embed(f"모스트 정보를 불러오는 중 오류: {str(e)}"))
