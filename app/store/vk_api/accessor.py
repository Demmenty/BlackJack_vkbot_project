import random
import typing
from pathlib import Path
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import BotMessage, Update
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application


IMG_DIR = Path(__file__).resolve().parent.parent / "game" / "img"
API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

        try:
            await self._get_long_poll_service()
        except Exception as error:
            self.logger.error("Exception", exc_info=error)

        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        url = self._build_query(
            host=API_PATH,
            method="groups.getLongPollServer",
            params={
                "group_id": self.app.config.bot.group_id,
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = (await response.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        url = self._build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "key": self.key,
                "ts": self.ts,
                "wait": 30,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])

            if raw_updates:
                updates = await self._prepare_updates(raw_updates)
                await self.app.store.bot_manager.handle_updates(updates)

    async def _prepare_updates(self, raw_updates: list) -> list[Update]:
        updates = []
        for update in raw_updates:
            if update["object"]["message"].get("action"):
                action_type = update["object"]["message"]["action"]["type"]
            else:
                action_type = ""

            upd = Update(
                id=update["object"]["message"]["id"],
                type=update["type"],
                action_type=action_type,
                from_id=update["object"]["message"]["from_id"],
                peer_id=update["object"]["message"]["peer_id"],
                text=update["object"]["message"]["text"],
            )
            updates.append(upd)
        return updates

    async def send_message(self, message: BotMessage) -> None:
        url = self._build_query(
            host=API_PATH,
            method="messages.send",
            params={
                "random_id": random.randint(1, 2**32),
                "peer_id": message.peer_id,
                "message": message.text,
                "keyboard": message.keyboard,
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

    async def get_username(self, user_id: int) -> str:
        """получить имя пользователя по его id в vk"""

        url = self._build_query(
            host=API_PATH,
            method="users.get",
            params={
                "user_ids": user_id,
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

        username = data["response"][0]["first_name"]
        return username
