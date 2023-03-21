from aiohttp.test_utils import TestClient

from web.config import Config
from tests.utils import ok_response


class TestAdminLogin:
    async def test_successful_login(self, cli: TestClient, config: Config):
        """проверка успешности входа админа с данными из конфига"""

        response = await cli.post(
            "/admin.login",
            json={
                "email": config.admin.email,
                "password": config.admin.password,
            },
        )
        assert response.status == 200

        data = await response.json()
        assert data == ok_response({"id": 1, "email": config.admin.email})

    async def test_missed_email(self, cli: TestClient):
        """проверка безуспешности входа админа без указания почты"""

        response = await cli.post(
            "/admin.login",
            json={
                "password": "qwerty",
            },
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["data"]["email"][0] == "Missing data for required field."

    async def test_missed_password(self, cli: TestClient):
        """проверка безуспешности входа админа без указания пароля"""

        response = await cli.post(
            "/admin.login",
            json={
                "email": "qwerty",
            },
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["data"]["password"][0] == "Missing data for required field."

    async def test_wrong_email(self, cli: TestClient, config: Config):
        """проверка безуспешности входа админа с неправильной почтой"""

        response = await cli.post(
            "/admin.login",
            json={
                "email": "qwerty",
                "password": config.admin.password,
            },
        )
        assert response.status == 403

        data = await response.json()
        assert data["status"] == "forbidden"

    async def test_wrong_password(self, cli: TestClient, config: Config):
        """проверка безуспешности входа админа с неправильным паролем"""

        response = await cli.post(
            "/admin.login",
            json={
                "email": config.admin.email,
                "password": "qwerty",
            },
        )
        assert response.status == 403

        data = await response.json()
        assert data["status"] == "forbidden"

    async def test_wrong_method(self, cli: TestClient, config: Config):
        """проверка безуспешности входа админа через метод GET"""

        response = await cli.get(
            "/admin.login",
            json={
                "email": config.admin.email,
                "password": config.admin.password,
            },
        )
        assert response.status == 405

        data = await response.json()
        assert data["status"] == "not_implemented"
