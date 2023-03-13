from aiohttp.web import HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema

from app.game.schemes import (
    ChatStatRequestSchema,
    ChatStatResponseSchema,
    PlayerStatSchema,
    UserStatRequestSchema,
    UserStatResponseSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ChatStatView(AuthRequiredMixin, View):
    @docs(
        tags=["chat_stat"],
        summary="get chat statistic",
        description="get chat statistic about the number of games played and the bank of the casino by vk chat id",
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
            "chat_id": chat.vk_id,
            "games_played": chat.games_played,
            "casino_cash": chat.casino_cash,
        }
        return json_response(data)


class UserStatView(AuthRequiredMixin, View):
    @docs(
        tags=["user_stat"],
        summary="get user statistic",
        description="get user statistic about the number of games he played, won and lost as player",
    )
    @request_schema(UserStatRequestSchema)
    @response_schema(UserStatResponseSchema, 200)
    async def get(self):
        request_user_id = self.request["data"]["user_id"]

        players = await self.request.app.store.game.get_players_of_user(
            request_user_id
        )

        if not players:
            raise HTTPNotFound(reason="user is not registered as a player")

        player_stat = [PlayerStatSchema().dump(player) for player in players]

        data = {
            "user_id": request_user_id,
            "number_of_gamechats": len(players),
            "player_stat": player_stat,
        }
        return json_response(data)
