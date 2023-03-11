import typing
from logging import getLogger

from app.store.bot.notifications import BotNotifier
from app.store.bot.phrases import BotPhrase
from app.store.game.router import GameEventRouter
from app.store.vk_api.dataclasses import BotMessage, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    """управление основными функциями бота"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notifier = BotNotifier(app)
        self.router = GameEventRouter(app)
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

        await self.notifier.no_personal_chating(update.peer_id)

    async def handle_chat_invite(self, update: Update) -> None:
        """обработка приглашения в беседу"""

        game_on = await self.app.store.game.is_game_on(update.peer_id)

        if game_on:
            await self.app.store.game_manager.notifier.bot_returning(
                update.peer_id
            )
            game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
            await self.app.store.game_manager.recovery(update.peer_id, game)
            return

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        if game:
            await self.notifier.meeting(update.peer_id, again=True)
        else:
            await self.notifier.meeting(update.peer_id)

        await self.app.store.game_handler.send_game_offer(update=update)

    async def handle_chat_msg(self, update: Update) -> None:
        """обработка сообщения в беседе"""

        update.text = self._clean_update_text(update.text)
        event = self.router.get_event(update.text)

        if event is None:
            return

        handler = self.router.route(event)
        await handler(update)

    def _clean_update_text(self, text: str) -> str:
        """возвращает полученный ботом текст очищенным
        от обращения, пробелов, знаков препинания и в нижнем регистре"""

        cleaned_text = (
            text.replace("[club218753438|@shadow_dementia]", "")
            .strip(" ,.!")
            .lower()
        )

        return cleaned_text
