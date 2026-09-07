import asyncio
import json

import discord
import requests

from config import GEMINI_KEY
from utils import Responder, crash_embed

# 키는 params로 붙이므로 URL에는 넣지 않는다.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite-preview-06-17:generateContent"


def setup_gemini_commands(bot):
    @bot.tree.command(name="ask", description="Gemini AI에게 질문해요!")
    async def ask_gemini(interaction: discord.Interaction, question: str):
        # 결과를 채널에 공개로 남긴다. 답변 생성이 3초를 넘기므로 먼저 응답을 유예한다.
        await interaction.response.defer()
        reply = Responder(interaction)
        try:
            headers = {
                "Content-Type": "application/json",
            }
            params = {"key": GEMINI_KEY}
            data = {
                "contents": [
                    {"parts": [{"text": "짧게 대답해줘. 질문 : " + question}]}
                ],
                "tools": [{"google_search": {}}],
            }
            response = await asyncio.to_thread(
                requests.post,
                GEMINI_API_URL,
                params=params,
                headers=headers,
                data=json.dumps(data),
                timeout=15,
            )
            if response.status_code != 200:
                await reply.send(
                    crash_embed(
                        f"Gemini API 오류: {response.status_code} {response.text[:1000]}"
                    )
                )
                return

            res_json = response.json()
            try:
                answer = res_json["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                # 안전 필터에 걸리면 candidates나 parts가 통째로 빠진 채로 온다.
                await reply.send(crash_embed("AI가 답변을 만들지 못했어요."))
                return

            # 필드(1024자)가 아니라 본문(4096자)에 담아야 답변이 덜 잘린다.
            body = f"**Q. {question}**\n\n{answer or '(빈 답변)'}"
            if len(body) > 4096:
                body = body[:4093] + "..."
            embed = discord.Embed(description=body, color=0x7AA600)
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url,
            )
            await reply.send(embed)
        except Exception as e:
            await reply.send(crash_embed(f"AI 답변 중 오류: {str(e)}"))
