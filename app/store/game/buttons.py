from ..vk_api.dataclasses import *


class GameButtons:
    def __init__(self):
        self.start = Button(action=Action(label="Начать игру"))
        self.start_already = Button(action=Action(label="Начать уже игру"))
        self.rules = Button(color="secondary", action=Action(label="Правила игры"))
        self.stop = Button(color="negative", action=Action(label="Остановить игру"))
        self.acceptgame = Button(action=Action(label="Я играю!"))
        self.abort = Button(color="negative", action=Action(label="Отменить игру"))
