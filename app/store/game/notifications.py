import typing

from app.store.vk_api.dataclasses import BotMessage, Keyboard

from .buttons import GameButton
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameNotifier:
    """уведомления в чат игры"""

    def __init__(self, app: "Application"):
        self.app = app

    async def game_is_on(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра уже идет"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_is_on,
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_is_off(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра сейчас не идет"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_is_off,
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_starting(self, peer_id: int) -> None:
        """уведомляет чат о начале игры"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_begun,
        )
        await self.app.store.vk_api.send_message(msg)

    async def waiting_players(self, peer_id: int) -> None:
        """уведомляет чат о начале набора игроков"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.wait_players,
            keyboard=Keyboard(
                buttons=[
                    [
                        GameButton.register,
                        GameButton.unregister,
                        GameButton.abort,
                    ]
                ]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_registered(self, peer_id: int, username: int) -> None:
        """уведомляет чат о регистрации игрока (передать его имя)"""
        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.player_registered,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_unregistered(self, peer_id: int, username: int) -> None:
        """уведомляет чат о том, что игрок не участвует (передать его имя)"""
        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.player_unregistered,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_registered_already(
        self, peer_id: int, username: int
    ) -> None:
        """уведомляет чат, что игрок уже зарегистрирован (передать имя)"""
        # TODO выслать кнопку "передумал" и реализовать такую функцию
        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.player_already_registered + username,
        )
        await self.app.store.vk_api.send_message(msg)

    async def no_players(self, peer_id: int) -> None:
        """уведомляет чат о том, что они петухи"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.no_players,
        )
        await self.app.store.vk_api.send_message(msg)

    async def active_players(self, peer_id: int, names: list[str]) -> None:
        """уведомляет чат о том, кто будет играть сейчас"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.active_players + ", ".join(names),
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_aborted(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра отменена (при наборе игроков)"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_abort,
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_canceled(self, peer_id: int, username: str) -> None:
        """уведомляет чат о том, что игра закончена (раньше времени)
        передать username = имя нажавшего на кнопку остановки"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_cancel + username,
        )
        await self.app.store.vk_api.send_message(msg)
