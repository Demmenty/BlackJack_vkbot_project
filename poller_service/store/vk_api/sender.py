import typing
from logging import getLogger

import aio_pika

from store.vk_api.dataclasses import Update

if typing.TYPE_CHECKING:
    from web.app import Application


class UpdateSender:
    """отправитель обновлений в брокер сообщений"""

    def __init__(self, app: "Application"):
        self.app = app
        self.connection = None
        self.channel = None
        self.routing_key = "vk_updates"
        self.logger = getLogger("update sender")
        app.on_startup.append(self.connect)

    async def connect(self, app: "Application"):
        self.connection = await aio_pika.connect_robust(
            self.app.config.rabbitmq.url
        )

        async with self.connection:
            self.channel = await self.connection.channel()

            await self.channel.default_exchange.publish(
                aio_pika.Message(body=f"Hello Rabbit!".encode()),
                routing_key=self.routing_key,
            )

    async def send_update(self, raw_update: dict) -> None:
        """отправляет update vk в брокер сообщений"""

        try:
            update = self._prepare_update(raw_update)
        except KeyError:
            self.logger.info(f"неожиданный формат update vk:\n{raw_update}")
            return

        self.connection = await aio_pika.connect_robust(
            self.app.config.rabbitmq.url
        )

        async with self.connection:
            self.channel = await self.connection.channel()

            await self.channel.default_exchange.publish(
                aio_pika.Message(body=update.json.encode()),
                routing_key=self.routing_key,
            )

    def _prepare_update(self, raw_update: dict) -> Update:
        if raw_update["object"]["message"].get("action"):
            action_type = raw_update["object"]["message"]["action"]["type"]
        else:
            action_type = ""

        update = Update(
            id=raw_update["object"]["message"]["id"],
            type=raw_update["type"],
            action_type=action_type,
            from_id=raw_update["object"]["message"]["from_id"],
            peer_id=raw_update["object"]["message"]["peer_id"],
            text=raw_update["object"]["message"]["text"],
        )

        return update
