import random
import typing
from logging import getLogger
from pathlib import Path
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import BotMessage, VKUser
from app.store.vk_api.poller import Poller
from app.store.vk_api.sender import UpdateSender

if typing.TYPE_CHECKING:
    from app.web.app import Application


IMG_DIR = Path(__file__).resolve().parent.parent / "game" / "img"
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

    async def send_message(self, message: BotMessage) -> None:
        """посылает сообщение вконтакте"""

        url = self._build_query(
            host=API_PATH,
            method="messages.send",
            params={
                "random_id": random.randint(1, 2**32),
                "peer_id": message.peer_id,
                "message": message.text,
                "keyboard": message.keyboard,
                "attachment": message.attachment,
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

    async def send_activity(self, vk_chat_id: int) -> bool:
        """посылает статус набора текста,
        возвращает истину об успешности запроса"""

        url = self._build_query(
            host=API_PATH,
            method="messages.setActivity",
            params={
                "type": "typing",
                "peer_id": vk_chat_id,
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

        return bool(data.get("response"))

    async def get_user(self, vk_user_id: int) -> VKUser:
        """получить датакласс пользователя по его id в vk"""

        url = self._build_query(
            host=API_PATH,
            method="users.get",
            params={
                "user_ids": vk_user_id,
                "fields": "sex",
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

        if (
            data["response"][0]["first_name"] == "Demmenty"
            or data["response"][0]["sex"] == 1
        ):
            sex = "female"
        else:
            sex = "male"

        user = VKUser(
            vk_user_id=data["response"][0]["id"],
            name=data["response"][0]["first_name"],
            sex=sex,
        )
        return user

    async def get_chat_users(self, vk_chat_id: int) -> list[VKUser] | None:
        """возвращает список участников чата или None, если не получилось"""
        url = self._build_query(
            host=API_PATH,
            method="messages.getConversationMembers",
            params={
                "peer_id": vk_chat_id,
                "fields": "sex",
                "access_token": self.app.config.bot.token,
            },
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

        if data.get("error"):
            return None

        users = data["response"]["profiles"]
        users_list = []

        for user in users:
            if user["first_name"] == "Demmenty" or user["sex"] == 1:
                sex = "female"
            else:
                sex = "male"

            user = VKUser(
                vk_user_id=user["id"],
                name=user["first_name"],
                sex=sex,
            )
            users_list.append(user)

        return users_list

    async def _get_upload_url(self) -> str:
        """получение адреса для загрузки вложения"""

        url = self._build_query(
            host=API_PATH,
            method="photos.getMessagesUploadServer",
            params={
                "peer_id": 0,
                "access_token": self.app.config.bot.token,
            },
        )

        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

        upload_url = data["response"]["upload_url"]
        return upload_url

    async def upload_photo(self, path: str) -> str | None:
        """загрузка фото в вк и получение его названия для прикрепления к сообщению
        если возврат None, значит что-то не получилось"""

        try:
            upload_url = await self._get_upload_url()
            files = {"photo": open(path, "rb")}

            async with self.session.post(upload_url, data=files) as response:
                response = await response.json(content_type=None)

            url = self._build_query(
                host=API_PATH,
                method="photos.saveMessagesPhoto",
                params={
                    "photo": response["photo"],
                    "server": response["server"],
                    "hash": response["hash"],
                    "access_token": self.app.config.bot.token,
                },
            )
            async with self.session.get(url) as response:
                data = await response.json()

                owner_id = data["response"][0]["owner_id"]
                photo_id = data["response"][0]["id"]

            return f"photo{owner_id}_{photo_id}"

        except Exception as error:
            self.logger.info(error)
            return None
