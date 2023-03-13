from aiohttp.web import HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema

from app.game.schemes import ChatStatRequestSchema, ChatStatResponseSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ChatStatView(AuthRequiredMixin, View):
    @docs(
        tags=["chat_stat"],
        summary="get chat statistic",
        description="get chat statistics about the number of games played and the bank of the casino by vk chat id",
    )
    @request_schema(ChatStatRequestSchema)
    @response_schema(ChatStatResponseSchema, 200)
    async def get(self):
        request_chat_id = self.request["data"]["chat_id"]

        chat = await self.request.app.store.game.get_chat_by_vk_id(
            request_chat_id
        )

        if not chat:
            raise HTTPNotFound(reason="no such chat registered")

        data = {
            "games_played": chat.games_played,
            "casino_cash": chat.casino_cash,
        }
        return json_response(data)
