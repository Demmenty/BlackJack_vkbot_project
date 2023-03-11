from asyncio import create_task, sleep as asleep
from logging import getLogger
from typing import Any, Awaitable, Callable

from app.store.game.dataclasses import GameWaitTask


class GameTimerManager:
    """управление таймерами игры"""

    def __init__(self):
        self.tasks: dict = {}
        self.logger = getLogger("game timer manager")

    async def start_timer(
        self,
        sec: int,
        vk_id: int,
        game_id: int,
        next_method: Callable[[int, int], Awaitable[Any]],
    ) -> None:
        """запускает фоновое ожидание и регистрирует его.
        если таймер вышел, а ожидание не cancel - запускает next_method и удаляет запись.
        """

        try:
            task = GameWaitTask(
                game_id=game_id,
                timer=create_task(asleep(sec)),
            )

            self.tasks.setdefault(game_id, [])
            self.tasks[game_id].append(task)

            await asleep(sec)

            if not task.timer.cancelled():
                self.tasks[game_id].remove(task)
                await next_method(vk_id, game_id)

        except Exception as error:
            self.logger.info("!!! start_timer error !!!", error)

    async def end_timer(self, game_id: int) -> None:
        """останавливает активное фоновое ожидание в игре.
        удаляет запись о нём соответственно id игры.
        """

        if not self.tasks.get(game_id):
            return

        try:
            for task in self.tasks[game_id]:
                if not task.timer.done():
                    task.timer.cancel()
                    self.tasks[game_id].remove(task)

        except Exception as error:
            self.logger.info("!!! end_timer error !!!", error)
