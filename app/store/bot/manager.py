import typing
from asyncio import sleep as asleep
from logging import getLogger

from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    """управление основными функциями бота"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        """сюда поступают все полученные события от вк"""

        for update in updates:
            # сообщение в личке
            if update.from_id == update.peer_id:
                await self.handle_private_msg(update)
            # приглашение в чат
            elif update.action_type == "chat_invite_user":
                await self.handle_chat_invite(update)
            # сообщение в чате
            else:
                await self.handle_chat_msg(update)

    async def handle_private_msg(self, update: Update):
        """обработка сообщения в личке"""

        if (
            update.text.lower() == "начать игру"
            or update.text.lower() == "начать уже игру"
        ):
            await self.app.store.game_manager.new_game(update)

        elif update.text.lower() == "правила игры":
            await self.app.store.game_manager.game_rules(update)

        else:
            await self.app.store.game_manager.offer_to_play(update)

    async def handle_chat_invite(self, update: Update):
        """обработка приглашения в беседу"""

        msg = BotMessage(
            peer_id=update.peer_id,
            text="Вечер в хату!",
        )
        await self.app.store.vk_api.send_message(msg)
        await asleep(4)
        await self.app.store.game_manager.offer_to_play(update)

    async def handle_chat_msg(self, update: Update):
        """обработка сообщения в беседе"""

        if (
            update.text.lower() == "[club218753438|@shadow_dementia] начать игру"
            or update.text.lower() == "[club218753438|@shadow_dementia] начать уже игру"
        ):
            await self.app.store.game_manager.new_game(update)

        elif update.text.lower() == "[club218753438|@shadow_dementia] правила игры":
            await self.app.store.game_manager.game_rules(update)

        elif update.text == "[club218753438|@shadow_dementia]":
            await self.app.store.game_manager.offer_to_play(update)
