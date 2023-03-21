import random
import typing
from logging import getLogger
from pathlib import Path
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from base.base_accessor import BaseAccessor
from store.bot.notifications import BotNotifier
from store.vk_api.dataclasses import BotMessage, VKUser

if typing.TYPE_CHECKING:
    from web.app import Application


IMG_DIR = Path(__file__).resolve().parent.parent / "game" / "img"
API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.logger = getLogger("vk api accessor")
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.ts: Optional[int] = None
        self.notifier = BotNotifier(app)

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

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

            if data.get("error"):
                await self.notifier.vk_error(
                    peer_id=message.peer_id,
                    error_code=data["error"]["error_code"],
                )

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

            if data.get("error"):
                await self.notifier.vk_error(
                    peer_id=vk_chat_id, error_code=data["error"]["error_code"]
                )

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
