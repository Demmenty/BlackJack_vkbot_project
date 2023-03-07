from dataclasses import dataclass
from asyncio import Task


@dataclass
class GameWaitTask:
    game_id: int
    type: str 
    task: Task

# TODO как-то ограничить варианты type ()