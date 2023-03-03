from ..vk_api.dataclasses import Action, Button


class GameButton:
    start = Button(action=Action(label="Начать игру"))
    rules = Button(color="secondary", action=Action(label="Правила игры"))
    stop = Button(color="negative", action=Action(label="Остановить игру"))
    register = Button(action=Action(label="Я в деле!"))
    unregister = Button(color="secondary", action=Action(label="Я пас"))
    abort = Button(color="negative", action=Action(label="Отменить игру"))
