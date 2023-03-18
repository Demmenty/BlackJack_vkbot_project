from aiohttp.web import HTTPBadRequest, HTTPNotFound
from aiohttp_apispec import docs, request_schema, response_schema

from app.game.schemes import (
    ChatStatRequestSchema,
    ChatStatResponseSchema,
    PlayerStatSchema,
    StartCashSchema,
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

        int32_max = 2147483647
        int32_min = -2147483648
        if request_chat_id > int32_max or request_chat_id < int32_min:
            raise HTTPNotFound(reason="invalid chat id")

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

        int32_max = 2147483647
        int32_min = -2147483648
        if request_user_id > int32_max or request_user_id < int32_min:
            raise HTTPNotFound(reason="invalid user id")

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


class StartCashView(AuthRequiredMixin, View):
    @docs(
        tags=["game_settings"],
        summary="get cash",
        description="get start cash for games",
    )
    @response_schema(StartCashSchema, 200)
    async def get(self):
        global_settings = (
            await self.request.app.store.game.get_global_settings()
        )

        data = {
            "start_cash": global_settings.start_cash,
        }
        return json_response(data)

    @docs(
        tags=["game_settings"],
        summary="set cash",
        description="set start cash for games",
    )
    @request_schema(StartCashSchema)
    @response_schema(StartCashSchema, 200)
    async def post(self):
        request_start_cash = self.request["data"]["start_cash"]

        if request_start_cash < 1:
            raise HTTPBadRequest(reason="Invalid integer")

        await self.request.app.store.game.set_start_cash(request_start_cash)
        global_settings = (
            await self.request.app.store.game.get_global_settings()
        )

        data = {
            "start_cash": global_settings.start_cash,
        }
        return json_response(data)
