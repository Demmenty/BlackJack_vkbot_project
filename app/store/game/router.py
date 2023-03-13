import typing
from collections.abc import Awaitable, Callable
from typing import Any

from app.store.game.events import GameEvent

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.game.handler import GameHandler
from app.store.vk_api.dataclasses import Update


class GameEventRouter:
    """перенаправитель игровых команд в соответствующий обработчик"""

    def __init__(self, app: "Application"):
        self.app = app
        self.events = GameEvent
        self.handler = GameHandler(app)

        self.HANDLERS: dict[GameEvent, Callable] = {
            GameEvent.start: self.handler.start_game,
            GameEvent.rules: self.handler.send_game_rules,
            GameEvent.register: self.handler.register_player,
            GameEvent.unregister: self.handler.unregister_player,
            GameEvent.bet: self.handler.accept_bet,
            GameEvent.cash: self.handler.send_player_cash,
            GameEvent.more_card: self.handler.deal_more_card,
            GameEvent.enough_cards: self.handler.stop_dealing_cards,
            GameEvent.hand: self.handler.send_player_hand,
            GameEvent.resent: self.handler.send_restore_command,
            GameEvent.restore_cash: self.handler.restore_game_and_cash,
            GameEvent.abort: self.handler.abort_game,
            GameEvent.stop: self.handler.cancel_game,
            GameEvent.statistic: self.handler.send_statistic,
            GameEvent.empty: self.handler.send_game_offer,
        }

    def get_event(self, text: str) -> GameEvent | None:
        """возвращает GameEvent, соответствующий переданному тексту, либо None"""

        if text.isdigit():
            return GameEvent.bet

        try:
            event = self.events(text)
            return event
        except ValueError:
            return None

    def route(self, event: GameEvent) -> Callable[[Update], Awaitable[Any]]:
        """возвращает назначенный на событие обработчик"""

        return self.HANDLERS[event]
