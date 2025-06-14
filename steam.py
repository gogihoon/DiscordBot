import discord
import urllib.parse
from urllib.request import urlopen, Request
import bs4
import re


def setup_steam_commands(bot):
    @bot.tree.command(name="steam", description="스팀에 있는 게임의 가격을 확인해요!")
    async def steam_price(interaction: discord.Interaction, game: str):
        try:
            # 1. 먼저 임시 응답(로딩 메시지) 보내기
            await interaction.response.send_message(
                embed=discord.Embed(description="검색 중입니다...", color=0x7AA600),
                ephemeral=True,
            )

            # 2. 실제 크롤링 및 처리
            enc_game = urllib.parse.quote(game)
            steam_url = (
                f"https://store.steampowered.com/search/?l=koreana&term={enc_game}"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            req = Request(steam_url, headers=headers)
            page = urlopen(req)
            html = page.read()
            soup = bs4.BeautifulSoup(html, "html5lib")
            titles = soup.find_all("span", class_="title")
            prices = soup.find_all(
                "div", class_="col search_price_discount_combined responsive_secondrow"
            )
            if titles:
                for i, (title, price_div) in enumerate(zip(titles, prices)):
                    price = price_div.text
                    price1 = re.sub("₩", "", price)
                    if len(price1.split()) == 3:
                        desc = f"{price1.split()[0]} 세일해서 {price1.split()[1]} -> {price1.split()[2]} 입니다!"
                    else:
                        desc = f"{price1.split()[0]} 입니다!"
                    embed = discord.Embed(
                        title=title.text, description=desc, color=0x7AA600
                    )
                    await interaction.followup.send(embed=embed)
                    if i >= 2:
                        break
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description="검색 결과가 없습니다.", color=0xFF0000
                    ),
                )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"스팀 정보를 가져오는 중 오류: {str(e)}",
                    color=0xFF0000,
                ),
            )
