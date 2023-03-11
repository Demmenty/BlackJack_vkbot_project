from app.store.game.events import GameEvent
from app.store.vk_api.dataclasses import Action, Button


class GameButton:
    start = Button(action=Action(label=GameEvent.start))
    rules = Button(color="secondary", action=Action(label=GameEvent.rules))
    register = Button(action=Action(label=GameEvent.register))
    unregister = Button(
        color="secondary", action=Action(label=GameEvent.unregister)
    )
    all_in = Button(action=Action(label=GameEvent.bet))
    show_cash = Button(color="secondary", action=Action(label=GameEvent.cash))
    one_more_card = Button(action=Action(label=GameEvent.more_card))
    enough_cards = Button(action=Action(label=GameEvent.enough_cards))
    show_hand = Button(color="secondary", action=Action(label=GameEvent.hand))
    resent = Button(color="negative", action=Action(label=GameEvent.resent))
    abort = Button(color="negative", action=Action(label=GameEvent.abort))
    stop = Button(color="negative", action=Action(label=GameEvent.stop))
    statistic = Button(
        color="secondary", action=Action(label=GameEvent.statistic)
    )
