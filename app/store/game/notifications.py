import typing

from app.store.vk_api.dataclasses import Action, BotMessage, Button, Keyboard

from .buttons import GameButton
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameNotifier:
    """посылает уведомления в чат игры"""

    def __init__(self, app: "Application"):
        self.app = app

    async def game_is_on(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра уже идет"""
        # TODO уведомлять, на какой стадии игра

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

    async def player_registered(self, peer_id: int, username: str) -> None:
        """уведомляет чат о регистрации игрока (передать его имя)"""
        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.player_registered,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_unregistered(self, peer_id: int, username: str) -> None:
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

    async def no_cash(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он не может играть без денег"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.no_cash,
            keyboard=Keyboard(
                buttons=[
                    [
                        GameButton.casino,
                    ]
                ]
            ).json,
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

    async def wait_bets(self, peer_id: int) -> None:
        """уведомляет чат о начале приема ставок"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.wait_bets,
            keyboard=Keyboard(
                buttons=[
                    [
                        Button(action=Action(label="10")),
                        Button(action=Action(label="50")),
                        Button(action=Action(label="100")),
                        Button(action=Action(label="300")),
                        Button(action=Action(label="500")),
                    ],
                    [
                        GameButton.all_in,
                        GameButton.show_cash,
                    ],
                ]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def to_much_bet(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он поставил больше, чем его баланс"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.to_much_bet + username,
        )
        await self.app.store.vk_api.send_message(msg)

    async def zero_bet(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он нельзя ставить ноль"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.zero_bet + username,
        )
        await self.app.store.vk_api.send_message(msg)

    async def no_bet(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он не сделал ставку,
        высылает предложение отправить или отказаться от участия"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.no_bet,
            keyboard=Keyboard(
                buttons=[
                    [
                        GameButton.unregister,
                        GameButton.abort,
                    ]
                ]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def bet_accepted(self, peer_id: int, username: str, bet: int) -> None:
        """уведомляет игрока, что его ставка принята"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.bet_accepted + str(bet),
        )
        await self.app.store.vk_api.send_message(msg)

    async def bet_accepted_already(
        self, peer_id: int, username: str, bet: int
    ) -> None:
        """уведомляет игрока, что его ставка принята"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.bet_accepted_already + str(bet),
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

    async def wrong_state(self, peer_id: int) -> None:
        """уведомляет чат о том, что запрошенная команда
        не подходит для текущей стадии игры в нем"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.wrong_state,
        )
        await self.app.store.vk_api.send_message(msg)
