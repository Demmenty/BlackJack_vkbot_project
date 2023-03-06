from ..vk_api.dataclasses import Action, Button


# TODO все возможные команды вынести в ЕНАМ в одно место, см.worknote
class GameButton:
    start = Button(action=Action(label="начать"))
    rules = Button(color="secondary", action=Action(label="правила"))
    stop = Button(color="negative", action=Action(label="прекратить"))
    register = Button(action=Action(label="играю"))
    unregister = Button(color="secondary", action=Action(label="пас"))
    abort = Button(color="negative", action=Action(label="отмена"))
    show_cash = Button(color="secondary", action=Action(label="кошель"))
    casino = Button(
        color="negative", action=Action(label="ебаный рот этого казино!")
    )
    all_in = Button(action=Action(label="ва-банк!"))
    one_more_card = Button(action=Action(label="карту"))
    enough_cards = Button(action=Action(label="довольно"))
    show_hand = Button(color="secondary", action=Action(label="рука"))
