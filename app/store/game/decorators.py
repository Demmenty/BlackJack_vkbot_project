import typing

from app.game.states import GameState
from app.store.vk_api.dataclasses import Update

if typing.TYPE_CHECKING:
    from app.store.game.manager import GameManager


def game_must_be_on(method):
    """если активной игры в этом чате не ведется -
    отменяет выполнение метода и посылает соответствующее уведомление"""

    async def wrapper(self: "GameManager", update: Update, *args, **kwargs):
        game_is_on = await self.app.store.game.is_game_on(update.peer_id)

        if not game_is_on:
            await self.notifier.game_is_off(peer_id=update.peer_id)
            return

        return await method(self, update, *args, **kwargs)

    return wrapper


def game_must_be_off(method):
    """если в чате ведется игра - отменяет выполнение метода"""

    async def wrapper(self: "GameManager", update: Update, *args, **kwargs):
        game_is_on = await self.app.store.game.is_game_on(update.peer_id)

        if game_is_on:
            return

        return await method(self, update, *args, **kwargs)

    return wrapper


def game_must_be_on_state(*states: tuple[GameState]):
    """если игра не на одной из переданных стадий - отменяет выполнение метода
    и посылает соответствующее уведомление"""

    def decorator(method):
        async def wrapper(self: "GameManager", update: Update, *args, **kwargs):
            game = await self.app.store.game.get_game_by_vk_id(update.peer_id)

            if game.state not in [state.name for state in states]:
                await self.notifier.wrong_state(peer_id=update.peer_id)
                return

            return await method(self, update, *args, **kwargs)

        return wrapper

    return decorator


# TODO @user_must_be_a_player
