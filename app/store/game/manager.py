import typing
from logging import getLogger

from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

from .buttons import GameButtons

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление ботом, связанное с игрой"""

    def __init__(self, app: "Application"):
        self.app = app
        self.button = GameButtons()
        self.logger = getLogger("handler")

    async def offer_to_play(self, update: Update):
        """предложение поиграть"""

        # TODO проверка, что игра не идет
        # TODO проверка, если в беседе уже была игра -> статистика
        msg = BotMessage(
            peer_id=update.peer_id,
            text="Сыграем в BlackJack? 😉",
            keyboard=Keyboard(
                buttons=[
                    [
                        self.button.start,
                        self.button.rules,
                    ]
                ]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def new_game(self, update: Update):
        """начало новой игры"""

        # TODO проверка, что игра не идет
        msg = BotMessage(
            peer_id=update.peer_id,
            text=("Да начнется битва! %0A" + "Весь чат в труху! %0A" + "но потом"),
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_rules(self, update: Update):
        """описание правил игры"""

        msg = BotMessage(
            peer_id=update.peer_id,
            text=(
                "В гугле забанили? %0A%0A" + "https://ru.wikihow.com/играть-в-блэкджек"
            ),
            keyboard=Keyboard(buttons=[[self.button.start_already]]).json,
        )
        await self.app.store.vk_api.send_message(msg)
