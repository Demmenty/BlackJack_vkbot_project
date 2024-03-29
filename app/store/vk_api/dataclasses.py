import json
from dataclasses import asdict, dataclass


# событие от вк
@dataclass
class Update:
    id: int
    type: str
    from_id: int
    peer_id: int
    action_type: str = ""
    text: str = ""

    @property
    def json(self):
        return json.dumps(asdict(self))


# клавиатура от бота
@dataclass
class Action:
    label: str
    type: str = "text"


@dataclass
class Button:
    action: Action
    color: str = "primary"


@dataclass
class Keyboard:
    buttons: list[Button]
    one_time: bool = False
    inline: bool = False

    @property
    def json(self):
        return json.dumps(asdict(self))


# сообщение от бота
@dataclass
class BotMessage:
    peer_id: int
    text: str
    keyboard: Keyboard = ""
    attachment: str = ""


# инфо о пользователе vk
@dataclass
class VKUser:
    vk_user_id: int
    name: str
    sex: str
