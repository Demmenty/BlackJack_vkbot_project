from aiohttp.web import HTTPForbidden
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import get_session, new_session

from app.game.schemes import StartCashSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class StartCashView(AuthRequiredMixin, View):
    @docs(
        tags=["game_settings"],
        summary="get cash",
        description="get start cash for games",
    )
    @response_schema(StartCashSchema, 200)
    async def get(self):
        start_cash = await self.request.app.store.game.get_start_cash()

        data = {
            "start_cash": start_cash,
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
        await self.request.app.store.game.set_start_cash(request_start_cash)
        start_cash = await self.request.app.store.game.get_start_cash()

        data = {
            "start_cash": start_cash,
        }
        return json_response(data)
