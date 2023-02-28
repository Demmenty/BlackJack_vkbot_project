from aiohttp.web import HTTPForbidden
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import get_session, new_session

from app.admin.schemes import AdminCurrentSchema, AdminLoginSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Admin login", description="Admin authorization")
    @request_schema(AdminLoginSchema)
    @response_schema(AdminCurrentSchema, 200)
    async def post(self):

        request_email = self.request["data"]["email"]
        request_password = self.request["data"]["password"]

        admin = await self.request.app.store.admin.get_by_email(request_email)

        if not admin:
            raise HTTPForbidden(reason="Wrong data, access denied")

        if not admin.is_password_valid(request_password):
            raise HTTPForbidden(reason="Wrong data, access denied")

        session = await new_session(request=self.request)
        admin_json = AdminCurrentSchema().dump(admin)
        session["admin"] = admin_json

        data = {
            "id": admin.id,
            "email": admin.email,
        }
        return json_response(data)


class AdminCurrentView(AuthRequiredMixin, View):
    @docs(
        tags=["admin"],
        summary="Admin view",
        description="Returns data about current admin, if authorized",
    )
    @response_schema(AdminCurrentSchema, 200)
    async def get(self):

        session = await get_session(self.request)
        request_email = session["admin"]["email"]
        admin = await self.request.app.store.admin.get_by_email(request_email)

        data = {
            "id": admin.id,
            "email": admin.email,
        }
        return json_response(data)
