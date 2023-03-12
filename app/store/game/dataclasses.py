from asyncio import Task
from dataclasses import dataclass


@dataclass
class GameWaitTask:
    game_id: int
    timer: Task
