import typing

from sqlalchemy.exc import OperationalError

if typing.TYPE_CHECKING:
    from store.game.accessor import GameAccessor


def catch_db_error(method):
    async def wrapper(self: "GameAccessor", *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        except OperationalError:
            return await method(self, *args, **kwargs)

    return wrapper

# TODO @user_must_be_a_player
