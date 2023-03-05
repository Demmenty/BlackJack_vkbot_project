import typing

from app.store.vk_api.dataclasses import Action, BotMessage, Button, Keyboard

from .buttons import GameButton
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


# TODO возможно, отправлять не инлайн кнопки определенных команд, например "остановить игру"
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

    async def waiting_bets(self, peer_id: int) -> None:
        """уведомляет чат о начале приема ставок"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.waiting_bets,
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

        if bet == 300:
            bet = "♂three hundred bucks♂"
        else:
            bet = "$" + str(bet)

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.bet_accepted + bet,
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

    async def game_aborted(self, peer_id: int, username: str = None) -> None:
        """уведомляет чат о том, что игра отменена (при наборе игроков)"""

        if username:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_abort + GamePhrase.to_blame + username,
            )
        else:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_abort,
            )
        await self.app.store.vk_api.send_message(msg)

    async def game_canceled(self, peer_id: int, username: str = None) -> None:
        """уведомляет чат о том, что игра закончена (раньше времени)"""

        if username:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_canceled + GamePhrase.to_blame + username,
            )
        else:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_canceled,
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

    async def dealing_started(self, peer_id: int) -> None:
        """уведомляет чат о том, что началась раздача карт"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.dealing_started,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_turn(self, peer_id: int, username: str) -> None:
        """уведомляет игрока о том, что его очередь брать карты"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.player_turn + username,
        )
        await self.app.store.vk_api.send_message(msg)

    async def not_your_turn(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он лезет без очереди"""

        msg = BotMessage(
            peer_id=peer_id, text=username + GamePhrase.not_your_turn
        )
        await self.app.store.vk_api.send_message(msg)

    async def cards_received(self, peer_id: int, cards: list[str]) -> None:
        """уведомляет о выпавших картах(карте)"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.cards_received + " ".join(cards),
        )
        await self.app.store.vk_api.send_message(msg)

    async def offer_a_card(self, peer_id: int) -> None:
        """выдает кнопки для запроса еще одной карты или отказа"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.offer_a_card,
            keyboard=Keyboard(
                buttons=[
                    [
                        GameButton.one_more_card,
                        GameButton.enough_cards,
                        GameButton.show_hand,
                    ]
                ]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_hand(
        self, peer_id: int, username: str, hand: list[str]
    ) -> None:
        """уведомляет игрока, какие карты у него на руках"""

        if hand:
            msg = BotMessage(
                peer_id=peer_id,
                text=username + GamePhrase.show_hand + " ".join(hand),
            )
        else:
            msg = BotMessage(
                peer_id=peer_id, text=GamePhrase.no_hand + username
            )
        await self.app.store.vk_api.send_message(msg)

    async def not_a_player(self, peer_id: int, username: str) -> None:
        """уведомляет пользователя, что он даже не игрок, даже не гражданин и даже не паладин"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.not_a_player,
        )
        await self.app.store.vk_api.send_message(msg)

    async def show_cash(self, peer_id: int, username: str, cash: int) -> None:
        """показывает игроку его воображаемые деньги"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.show_cash + str(cash),
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_blackjack(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что у него очко"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.blackjack,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_blackjack(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что у него очко"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.blackjack,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_overflow(self, peer_id: int) -> None:
        """уведомляет игрока, что у него получилось > 21"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.overflow,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_loss(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он проиграл"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.player_loss,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_draw(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что ничья"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.player_draw + username,
        )
        await self.app.store.vk_api.send_message(msg)

    async def player_win(self, peer_id: int, username: str) -> None:
        """уведомляет игрока, что он выиграл"""

        msg = BotMessage(
            peer_id=peer_id,
            text=username + GamePhrase.player_win,
        )
        await self.app.store.vk_api.send_message(msg)

    async def deal_to_dealer(self, peer_id: int) -> None:
        """уведомляет чат о начале раздачи карт дилеру"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.deal_to_dealer,
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_ended(self, peer_id: int) -> None:
        """уведомляет чат о завершении игры"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_ended,
        )
        await self.app.store.vk_api.send_message(msg)

    async def game_offer(self, peer_id: int, again: bool = False) -> None:
        """предлагает сыграть в Black Jack"""

        # TODO если again -> др кнопки?

        if again:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_offer_again,
                keyboard=Keyboard(
                    buttons=[[GameButton.start, GameButton.rules]]
                ).json,
            )
        else:
            msg = BotMessage(
                peer_id=peer_id,
                text=GamePhrase.game_offer,
                keyboard=Keyboard(
                    buttons=[[GameButton.start, GameButton.rules]]
                ).json,
            )
        await self.app.store.vk_api.send_message(msg)
