import asyncio
import re
import urllib.parse
from urllib.request import urlopen, Request

import bs4
import discord

from utils import Responder, crash_embed, error_embed


def setup_steam_commands(bot):
    @bot.tree.command(name="steam", description="스팀에 있는 게임의 가격을 확인해요!")
    async def steam_price(interaction: discord.Interaction, game: str):
        # 결과를 채널에 공개로 남긴다. 크롤링이 3초를 넘길 수 있어 먼저 응답을 유예한다.
        await interaction.response.defer()
        reply = Responder(interaction)
        try:
            enc_game = urllib.parse.quote(game)
            steam_url = (
                f"https://store.steampowered.com/search/?l=koreana&term={enc_game}"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            req = Request(steam_url, headers=headers)

            def fetch():
                with urlopen(req, timeout=10) as page:
                    return page.read()

            html = await asyncio.to_thread(fetch)
            soup = bs4.BeautifulSoup(html, "html5lib")

            sent = 0
            # 제목과 가격을 각각 모아 zip 하면 가격이 없는 항목에서 짝이 어긋나므로
            # 검색 결과 한 줄씩 순회한다.
            for row in soup.find_all("a", class_="search_result_row"):
                title = row.find("span", class_="title")
                price_div = row.find("div", class_="search_price_discount_combined")
                if title is None or price_div is None:
                    continue
                parts = re.sub("₩", "", price_div.text).split()
                if not parts:
                    # 출시 예정이라 가격 표기가 없는 항목은 건너뛴다.
                    continue
                if len(parts) == 3:
                    desc = f"{parts[0]} 세일해서 {parts[1]} -> {parts[2]} 입니다!"
                else:
                    desc = f"{parts[0]} 입니다!"
                await reply.send(
                    discord.Embed(title=title.text, description=desc, color=0x7AA600)
                )
                sent += 1
                if sent >= 3:
                    break

            if sent == 0:
                await reply.send(error_embed(f'"{game}" 검색 결과가 없습니다.'))
        except Exception as e:
            await reply.send(crash_embed(f"스팀 정보를 가져오는 중 오류: {str(e)}"))
