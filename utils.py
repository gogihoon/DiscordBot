import discord


class Responder:
    """defer() 이후의 응답을 순서에 맞게 안전하게 내보낸다.

    - 첫 메시지는 defer가 만들어 둔 '생각 중' 자리를 채운다.
      (followup으로 보내면 그 자리가 계속 남아 있는다)
    - 두 번째부터는 followup으로 이어 보낸다.
    - 이미 응답한 뒤에 response.send_message()를 다시 부르면 InteractionResponded가
      나므로, except 블록에서도 이 객체를 통해 보내야 한다.

    공개/비공개는 defer(ephemeral=...)에서 정해지고 첫 메시지는 그 설정을 따른다.
    """

    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.original_used = False

    async def send(self, embed: discord.Embed, *, ephemeral: bool = False):
        try:
            if not self.interaction.response.is_done():
                await self.interaction.response.send_message(
                    embed=embed, ephemeral=ephemeral
                )
            elif not self.original_used:
                await self.interaction.edit_original_response(embed=embed)
            else:
                await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)
        except discord.HTTPException:
            return
        self.original_used = True


def error_embed(title: str, description: str | None = None, *, thumbnail: bool = True):
    """실패 안내용 임베드를 만든다."""
    embed = discord.Embed(title=title, description=description, color=0x7AA600)
    if thumbnail:
        embed.set_thumbnail(url="https://i.imgur.com/KBfn8V8.png")
    return embed


def crash_embed(description: str):
    """예상하지 못한 예외를 알리는 임베드를 만든다."""
    return discord.Embed(description=description, color=0xFF0000)
