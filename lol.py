import discord
import requests
from config import RIOT_KEY, lol_version


def setup_lol_commands(bot):
    async def riot_get_puuid(nickname: str, tag: str):
        URL = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{nickname}/{tag}"
        try:
            res = requests.get(URL, headers={"X-Riot-Token": RIOT_KEY})
            if res.status_code == 200:
                data = res.json()
                return data["puuid"]
        except Exception:
            return None

    @bot.tree.command(name="tier", description="롤 랭크 티어를 확인해요!")
    async def league_tier(interaction: discord.Interaction, nickname: str, tag: str):
        try:
            puuid = await riot_get_puuid(nickname, tag)
            if not puuid:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="닉네임과 태그를 정확히 입력해주세요!", color=0x7AA600
                    ).set_thumbnail(url="https://i.imgur.com/KBfn8V8.png"),
                    ephemeral=True,
                )
                return
            URL = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            res = requests.get(URL, headers={"X-Riot-Token": RIOT_KEY})
            if res.status_code != 200:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="입력하신 닉네임과 태그를 다시 확인해 주세요.",
                        color=0x7AA600,
                    ).set_thumbnail(url="https://i.imgur.com/KBfn8V8.png"),
                    ephemeral=True,
                )
                return
            data = res.json()
            embed = discord.Embed(
                title="랭크 전적!",
                description=f"{nickname} 의 전적을\n불러오고 있어요!",
                color=0x7AA600,
            )
            embed.set_thumbnail(
                url=f"http://ddragon.leagueoflegends.com/cdn/{lol_version[0]}/img/profileicon/{data['profileIconId']}.png"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            URL = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/{data['id']}"
            rankinfo = requests.get(URL, headers={"X-Riot-Token": RIOT_KEY})
            rankData = rankinfo.json()

            tier_img = {
                "IRON": "https://i.imgur.com/jMCF0jp.png",
                "BRONZE": "https://i.imgur.com/Yr5zIKg.png",
                "SILVER": "https://i.imgur.com/ydwcOgT.png",
                "GOLD": "https://i.imgur.com/Qpmwjxg.png",
                "EMERALD": "https://i.imgur.com/JIkmK7x.png",
                "PLATINUM": "https://i.imgur.com/IhnXzoB.png",
                "DIAMOND": "https://i.imgur.com/1uYnavY.png",
                "MASTER": "https://i.imgur.com/ScVNf2g.png",
                "GRANDMASTER": "https://i.imgur.com/TyASwqZ.png",
                "CHALLENGER": "https://i.imgur.com/Zfvk2BJ.png",
            }

            for i in rankData:
                if i["queueType"] in ["RANKED_SOLO_5x5", "RANKED_FLEX_SR"]:
                    qtype = (
                        "솔로랭크"
                        if i["queueType"] == "RANKED_SOLO_5x5"
                        else "자유랭크"
                    )
                    embed = discord.Embed(
                        title=qtype,
                        description=f' :trophy:  : {i["tier"]} {i["rank"]}\n'
                        f' :v:  : {i["wins"]} :poop:  : {i["losses"]}\n'
                        f' :dart:  : {i["wins"] / (i["wins"] + i["losses"]) * 100:.2f}%',
                        color=0x7AA600,
                    )
                    embed.set_thumbnail(url=tier_img.get(i["tier"], ""))
                    await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"티어 정보를 불러오는 중 오류: {str(e)}",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )

    @bot.tree.command(name="most", description="롤 모스트 챔피언을 확인해요!")
    async def league_most(interaction: discord.Interaction, nickname: str, tag: str):
        try:
            puuid = await riot_get_puuid(nickname, tag)
            if not puuid:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="닉네임과 태그를 정확히 입력해주세요!", color=0x7AA600
                    ).set_thumbnail(url="https://i.imgur.com/KBfn8V8.png"),
                    ephemeral=True,
                )
                return
            URL = f"https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
            res = requests.get(URL, headers={"X-Riot-Token": RIOT_KEY})
            mostInfo = res.json()
            await interaction.response.send_message(
                embed=discord.Embed(title=f"{nickname}의 모스트", color=0x7AA600),
                ephemeral=True,
            )
            req = requests.get(
                f"http://ddragon.leagueoflegends.com/cdn/{lol_version[0]}/data/ko_KR/champion.json"
            )
            champ_data = req.json()["data"]
            key_to_name = {v["key"]: k for k, v in champ_data.items()}
            for j, i in enumerate(mostInfo[:3]):
                champ_name = champ_data[key_to_name[str(i["championId"])]]["name"]
                champ_level = i["championLevel"]
                champ_points = i["championPoints"]
                img = champ_data[key_to_name[str(i["championId"])]]["image"]["full"]
                embed = discord.Embed(
                    title=f"모스트{j + 1}은(는) {champ_name}에요!",
                    description=f"{champ_level}레벨\n{champ_points} 포인트",
                    color=0x7AA600,
                )
                embed.set_thumbnail(
                    url=f"http://ddragon.leagueoflegends.com/cdn/{lol_version[0]}/img/champion/{img}"
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"모스트 정보를 불러오는 중 오류: {str(e)}",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
