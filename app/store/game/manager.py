import typing
from asyncio import sleep as asleep
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

    async def offer_to_play(self, update: Update) -> None:
        """предложение поиграть"""

        # TODO проверка, что игра не идет
        # TODO проверка, если в беседе уже была игра -> статистика
        msg = BotMessage(
            peer_id=update.peer_id,
            text="Сыграем в BlackJack? 😉",
            keyboard=Keyboard(buttons=[[self.button.start, self.button.rules]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def new_game(self, update: Update) -> None:
        """начало новой игры"""

        # проверка, что игра не идет
        game = await self.app.store.game.get_by_peer(update.peer_id)

        if game.state != "inactive":
            msg = BotMessage(
                peer_id=update.peer_id,
                text=("Игра уже идёт, алло 🤨"),
            )
            await self.app.store.vk_api.send_message(msg)

        else:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=("Да начнется битва! %0A" + "Весь чат в труху! %0A"),
            )
            await self.app.store.vk_api.send_message(msg)
            await asleep(3)

            # TODO кнопка отказа, чтобы не ждать:
            # просьба сделать админом -> получить участников беседы -> сравнить
            msg = BotMessage(
                peer_id=update.peer_id,
                text=("Кто будет участвовать? %0A" + "Жду заявок 15 секунд..."),
                keyboard=Keyboard(
                    buttons=[[self.button.acceptgame, self.button.abort]]
                ).json,
            )
            await self.app.store.vk_api.send_message(msg)
            await self.app.store.game.change_state(game.id, "define_players")

            # TODO поставить таймер


    async def game_rules(self, update: Update) -> None:
        """описание правил игры"""

        # TODO проверить статус игры -> отправлять кнопку только если "inactive"

        msg = BotMessage(
            peer_id=update.peer_id,
            text=(
                "В гугле забанили? %0A%0A" + "https://ru.wikihow.com/играть-в-блэкджек"
            ),
            keyboard=Keyboard(buttons=[[self.button.start_already]]).json,
        )
        await self.app.store.vk_api.send_message(msg)
