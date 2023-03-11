from enum import StrEnum


class GameEvent(StrEnum):
    "команды в чате, вызывающие игровые события"

    start = "начать"
    rules = "правила"
    register = "играю"
    unregister = "пас"
    bet = "ва-банк"
    cash = "кошель"
    more_card = "карту"
    enough_cards = "довольно"
    hand = "рука"
    resent = "ебаный рот этого казино"
    restore_cash = "converta tempus"
    abort = "отмена"
    stop = "прекратить это безумие"
    statistic = "статистика"
    empty = ""
