import typing
from asyncio import sleep as asleep
from collections.abc import Awaitable, Callable
from typing import Any

if typing.TYPE_CHECKING:
    from store.bot.notifications import BotNotifier


# декоратор для Notifier
def bot_typing(method: Callable[[int, Any], Awaitable[None]], sec: int = 3):
    """посылает инфо о печатании и ждет переданное количество секунд.
    по умолчанию = 3 секунды"""

    async def wrapper(self: "BotNotifier", *args, **kwargs):
        vk_chat_id = kwargs.get("peer_id")
        if not vk_chat_id:
            vk_chat_id = args[0]

        await self.app.store.vk_api.send_activity(vk_chat_id)
        await asleep(sec)

        return await method(self, *args, **kwargs)

    return wrapper
