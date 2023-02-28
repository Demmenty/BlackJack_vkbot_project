import typing
from logging import getLogger

from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

from .buttons import GameButton
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление ботом, связанное с игрой"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("handler")

    async def offer_game(self, update: Update) -> None:
        """отправляет в беседу предложение поиграть"""

        # TODO проверка, что игра не идет
        # TODO проверка, если в беседе уже была игра -> статистика
        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.game_offer,
            keyboard=Keyboard(buttons=[[GameButton.start, GameButton.rules]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def start_new_game(self, update: Update) -> None:
        """начало новой игры"""

        # проверка, что игра не идет
        game = await self.app.store.game.get_by_peer(update.peer_id)

        if game.state != "inactive":
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_is_on,
            )
            await self.app.store.vk_api.send_message(msg)
            return

        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.game_begun,
        )
        await self.app.store.vk_api.send_message(msg)

        # TODO кнопка отказа, чтобы не ждать:
        # просьба сделать админом -> получить участников беседы -> сравнить
        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.wait_players,
            keyboard=Keyboard(
                buttons=[[GameButton.acceptgame, GameButton.abort]]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)
        await self.app.store.game.change_state(game.id, "define_players")

        # TODO поставить таймер

    async def send_game_rules(self, update: Update) -> None:
        """описание правил игры"""

        # TODO проверить статус игры -> отправлять кнопку только если "inactive"

        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.rules,
            keyboard=Keyboard(buttons=[[GameButton.start]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def cancel_game(self, update: Update) -> None:
        """заканчивает активную игру в чате переданного update"""

        game = await self.app.store.game.get_by_peer(update.peer_id)
        if game.state == "define_players":
            await self.app.store.game.change_state(game.id, "inactive")
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_abort,
            )
            await self.app.store.vk_api.send_message(msg)
