import typing

from app.store.bot.decorators import bot_typing
from app.store.bot.phrases import BotPhrase
from app.store.vk_api.dataclasses import BotMessage

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotNotifier:
    """посылает уведомления в чат"""

    def __init__(self, app: "Application"):
        self.app = app

    @bot_typing
    async def meeting(self, peer_id: int, again: bool = False) -> None:
        """приветствует чат, так сказать"""

        msg = BotMessage(
            peer_id=peer_id,
            text=BotPhrase.meeting(again),
        )
        await self.app.store.vk_api.send_message(msg)

    async def no_personal_chating(self, peer_id: int) -> None:
        """уведомляет о том, что бот работает только в чатах"""

        msg = BotMessage(
            peer_id=peer_id,
            text=BotPhrase.no_personal_chating(),
        )
        await self.app.store.vk_api.send_message(msg)

    async def vk_error(self, peer_id: int, error_code: int) -> None:
        """уведомляет о том, что пришла ошибка от vk вместо ответа"""

        msg = BotMessage(
            peer_id=peer_id,
            text=BotPhrase.vk_error(error_code),
        )
        await self.app.store.vk_api.send_message(msg)
