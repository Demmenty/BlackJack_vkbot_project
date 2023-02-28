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

    async def handle_updates(self, updates: list[Update]) -> None:
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

    async def handle_private_msg(self, update: Update) -> None:
        """обработка сообщения в личке"""

        msg = BotMessage(
            peer_id=update.peer_id,
            text=(
                "Создайте чат и пригласите меня, тогда сможем поиграть в BlackJack %0A"
                + "Больше я ничего пока не умею :("
            ),
        )
        await self.app.store.vk_api.send_message(msg)

    async def handle_chat_invite(self, update: Update) -> None:
        """обработка приглашения в беседу"""

        msg = BotMessage(
            peer_id=update.peer_id,
            text="Вечер в хату!",
        )
        await self.app.store.vk_api.send_message(msg)
        await asleep(4)

        game = await self.app.store.game.get_by_peer(update.peer_id)

        if game.state == "inactive":
            await self.app.store.game_manager.offer_to_play(update)
            

    async def handle_chat_msg(self, update: Update) -> None:
        """обработка сообщения в беседе"""

        if (
            update.text.lower() == "[club218753438|@shadow_dementia] начать игру"
            or update.text.lower() == "[club218753438|@shadow_dementia] начать уже игру"
        ):
            await self.app.store.game_manager.new_game(update)

        elif update.text.lower() == "[club218753438|@shadow_dementia] правила игры":
            await self.app.store.game_manager.game_rules(update)

        elif update.text == "[club218753438|@shadow_dementia]":
            # TODO настроить варианты в зависимости от состояния игры
            await self.app.store.game_manager.offer_to_play(update)

        # TODO обработка "отменить игру"
        # TODO обработка присоединения игроков
