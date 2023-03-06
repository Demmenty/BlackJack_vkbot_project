import typing
from logging import getLogger

from app.store.bot.phrases import BotPhrase
from app.store.vk_api.dataclasses import BotMessage, Update

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
            text=BotPhrase.pm_msg,
        )
        await self.app.store.vk_api.send_message(msg)

    async def handle_chat_invite(self, update: Update) -> None:
        """обработка приглашения в беседу"""

        msg = BotMessage(
            peer_id=update.peer_id,
            text=BotPhrase.greeting,
        )
        await self.app.store.vk_api.send_message(msg)
        await self.app.store.game_handler.send_game_offer(update)

    async def handle_chat_msg(self, update: Update) -> None:
        """обработка сообщения в беседе"""

        update.text = self._cleaned_update_text(update.text)

        if update.text.isdigit():
            await self.app.store.game_handler.accept_bet(update)
            return

        # TODO все возможные команды вынести в ЕНАМ в одно место, см.worknote
        game_handlers = {
            "начать игру": self.app.store.game_handler.start_game,
            "правила игры": self.app.store.game_handler.send_game_rules,
            "остановить игру": self.app.store.game_handler.cancel_game,
            "отменить игру": self.app.store.game_handler.abort_game,
            "я в деле!": self.app.store.game_handler.register_player,
            "я пас": self.app.store.game_handler.unregister_player,
            "посмотреть баланс": self.app.store.game_handler.send_player_cash,
            "ва-банк!": self.app.store.game_handler.accept_bet,
            "еще карту": self.app.store.game_handler.deal_more_card,
            "ещё карту": self.app.store.game_handler.deal_more_card,
            "хватит": self.app.store.game_handler.stop_dealing_cards,
            "посмотреть руку": self.app.store.game_handler.send_player_hand,
            "": self.app.store.game_handler.send_game_offer,
        }

        handler = game_handlers.get(update.text)

        if handler:
            await handler(update)

    def _cleaned_update_text(self, text: str) -> str:
        """возвращает полученный ботом текст
        очищенным от обращения, пробелов и в нижнем регистре"""

        cleaned_text = (
            text.replace("[club218753438|@shadow_dementia]", "").strip().lower()
        )

        return cleaned_text
