import typing
from logging import getLogger
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from store.base.base_accessor import BaseAccessor
from store.vk_api.poller import Poller
from store.vk_api.sender import UpdateSender

if typing.TYPE_CHECKING:
    from web.app import Application


API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.logger = getLogger("vk api accessor")
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None
        self.sender = UpdateSender(app)

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

            if data.get("failed"):
                try:
                    await self._get_long_poll_service()
                    self.logger.info("long_poll_service renewed")
                except Exception as error:
                    self.logger.error("Exception", exc_info=error)
                return

            self.ts = data["ts"]

            raw_updates = data.get("updates", [])

            if raw_updates:
                for raw_update in raw_updates:
                    await self.sender.send_update(raw_update)
