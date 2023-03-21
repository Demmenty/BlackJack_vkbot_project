import json
import typing
from logging import getLogger

import aio_pika

from store.vk_api.dataclasses import Update

if typing.TYPE_CHECKING:
    from web.app import Application


class UpdateReceiver:
    """получатель обновлений из брокера сообщений"""

    def __init__(self, app: "Application"):
        self.app = app
        self.queue_name: str = "vk_updates"
        self.logger = getLogger("update receiver")
        app.on_startup.append(self.connect)

    async def connect(self, app: "Application"):
        connection = await aio_pika.connect_robust(self.app.config.rabbitmq.url)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(self.queue_name, durable=True)
        await queue.consume(self.route_update)

    async def route_update(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        """направляет полученный update в обработчик (если это update)"""

        async with message.process():
            try:
                data = json.loads(message.body.decode())
                update = Update(**data)
                await self.app.store.bot_manager.handle_update(update)

            except json.decoder.JSONDecodeError:
                self.logger.info(f"{message.body.decode()}")
