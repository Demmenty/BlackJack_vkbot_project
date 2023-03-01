from ..vk_api.dataclasses import Button, Action


class GameButton:
    start = Button(action=Action(label="Начать игру"))
    rules = Button(color="secondary", action=Action(label="Правила игры"))
    stop = Button(color="negative", action=Action(label="Остановить игру"))
    acceptgame = Button(action=Action(label="Я играю!"))
    abort = Button(color="negative", action=Action(label="Отменить игру"))
