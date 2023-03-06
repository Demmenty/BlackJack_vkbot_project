from ..vk_api.dataclasses import Action, Button


class GameButton:
    start = Button(action=Action(label="Начать игру"))
    rules = Button(color="secondary", action=Action(label="Правила игры"))
    stop = Button(color="negative", action=Action(label="Остановить игру"))
    register = Button(action=Action(label="Я в деле!"))
    unregister = Button(color="secondary", action=Action(label="Я пас"))
    abort = Button(color="negative", action=Action(label="Отменить игру"))
    show_cash = Button(
        color="secondary", action=Action(label="Посмотреть баланс")
    )
    casino = Button(
        color="negative", action=Action(label="Ебаный рот этого казино!")
    )
    all_in = Button(action=Action(label="Ва-банк!"))
    one_more_card = Button(action=Action(label="Еще карту"))
    enough_cards = Button(action=Action(label="Хватит"))
    show_hand = Button(
        color="secondary", action=Action(label="Посмотреть руку")
    )
