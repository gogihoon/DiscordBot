import asyncio
import urllib.parse
from urllib.request import urlopen, Request

import bs4
import discord

from utils import Responder, crash_embed, error_embed


def setup_weather_commands(bot):
    @bot.tree.command(name="weather", description="날씨를 확인해요!")
    async def show_weather(interaction: discord.Interaction, location: str):
        # 결과를 채널에 공개로 남긴다. 크롤링이 3초를 넘길 수 있어 먼저 응답을 유예한다.
        await interaction.response.defer()
        reply = Responder(interaction)
        try:
            enc_location = urllib.parse.quote(location + "+날씨")
            temp_url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query={enc_location}"
            headers = {"User-Agent": "Mozilla/5.0"}
            req = Request(temp_url, headers=headers)

            def fetch():
                with urlopen(req, timeout=10) as page:
                    return page.read()

            html = await asyncio.to_thread(fetch)
            soup = bs4.BeautifulSoup(html, "html5lib")

            summary = soup.find("p", class_="summary")
            title = soup.find("div", class_="temperature_text")
            descs = soup.find_all("dd", class_="desc")
            temp_info = summary.text.split() if summary else []
            # 검색 결과에 날씨 카드가 없으면 필요한 요소가 통째로 비어 있다.
            if title is None or len(temp_info) < 4 or len(descs) < 3:
                await reply.send(
                    error_embed(
                        "날씨 정보를 찾지 못했어요!", "지역 이름을 다시 확인해 주세요."
                    )
                )
                return

            embed = discord.Embed(
                title=title.text,
                description=(
                    f"{temp_info[0]}{temp_info[1]}{temp_info[2]}!\n"
                    f'날씨는 "{temp_info[3]}"!\n'
                    f"체감 온도는 {descs[0].text}!\n"
                    f"습도는 {descs[1].text}!\n"
                    f"풍속은 {descs[2].text}!\n"
                ),
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            await reply.send(embed)
        except Exception as e:
            await reply.send(crash_embed(f"날씨 정보를 가져오는 중 오류: {str(e)}"))
