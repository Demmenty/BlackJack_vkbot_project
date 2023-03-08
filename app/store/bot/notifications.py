import typing

from app.store.bot.phrases import BotPhrase
from app.store.vk_api.dataclasses import BotMessage

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotNotifier:
    """посылает уведомления в чат"""

    def __init__(self, app: "Application"):
        self.app = app

    async def meeting(self, peer_id: int, again: bool = False) -> None:
        """приветствует чат, так сказать"""

        msg = BotMessage(
            peer_id=peer_id,
            text=BotPhrase.meeting(again),
        )
        await self.app.store.vk_api.send_message(msg)
