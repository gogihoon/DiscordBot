import discord
import requests
import json
from config import GEMINI_KEY

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite-preview-06-17:generateContent?key="
    + GEMINI_KEY
)


def setup_gemini_commands(bot):
    @bot.tree.command(name="ask", description="Gemini AI에게 질문해요!")
    async def ask_gemini(interaction: discord.Interaction, question: str):
        try:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="AI가 답변을 생성 중입니다...", color=0x7AA600
                ),
                ephemeral=True,
            )

            headers = {
                "Content-Type": "application/json",
            }
            params = {"key": GEMINI_KEY}
            data = {
                "contents": [
                    {"parts": [{"text": "짧게 대답해줘. 질문 : " + question}]}
                ],
                "tools": [{"goggle_search": {}}],
            }
            response = requests.post(
                GEMINI_API_URL,
                params=params,
                headers=headers,
                data=json.dumps(data),
                timeout=15,
            )
            if response.status_code == 200:
                res_json = response.json()
                answer = res_json["candidates"][0]["content"]["parts"][0]["text"]
                embed = discord.Embed(color=0x7AA600)
                embed.set_author(
                    name=interaction.user.display_name,
                    icon_url=(
                        interaction.user.avatar.url
                        if interaction.user.avatar
                        else discord.Embed.Empty
                    ),
                )
                embed.add_field(
                    name="질문",
                    value=question,
                    inline=False,
                )
                embed.add_field(
                    name="AI 답변",
                    value=answer[:1024],
                    inline=False,
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        description=f"Gemini API 오류: {response.status_code} {response.text}",
                        color=0xFF0000,
                    )
                )
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"AI 답변 중 오류: {str(e)}", color=0xFF0000
                )
            )
