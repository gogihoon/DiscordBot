import discord
import urllib.parse
from urllib.request import urlopen, Request
import bs4


def setup_weather_commands(bot):
    @bot.tree.command(name="weather", description="날씨를 확인해요!")
    async def show_weather(interaction: discord.Interaction, location: str):
        try:
            enc_location = urllib.parse.quote(location + "+날씨")
            temp_url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query={enc_location}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            req = Request(temp_url, headers=headers)
            page = urlopen(req)
            html = page.read()
            soup = bs4.BeautifulSoup(html, "html5lib")
            temp_info = soup.find("p", class_="summary").text.split()
            embed = discord.Embed(
                title=soup.find("div", class_="temperature_text").text,
                description=f'{temp_info[0]}{temp_info[1]}{temp_info[2]}!\n날씨는 "{temp_info[3]}"!\n'
                f"체감 온도는 {soup.find_all('dd', class_='desc')[0].text}!\n"
                f"습도는 {soup.find_all('dd', class_='desc')[1].text}!\n"
                f"풍속은 {soup.find_all('dd', class_='desc')[2].text}!\n",
                color=0x7AA600,
            )
            embed.set_thumbnail(url="https://imgur.com/jmu6tXm.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"날씨 정보를 가져오는 중 오류: {str(e)}",
                    color=0xFF0000,
                ),
                ephemeral=True,
            )
