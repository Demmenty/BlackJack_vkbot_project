from aiohttp.test_utils import TestClient

from app.store import Store
from tests.utils import ok_response


class TestStartCashView:
    async def test_succesful_startcash_get(
        self, authed_cli: TestClient, store: Store
    ):
        """проверка успешности получения данных"""

        response = await authed_cli.get("/game.start_cash")

        assert response.status == 200

        global_settings = await store.game.get_global_settings()

        data = await response.json()
        assert data == ok_response({"start_cash": global_settings.start_cash})

    async def test_unauthorized_startcash_get(self, cli: TestClient):
        """проверка безуспешности получения данных
        неавторизованными пользователями"""

        response = await cli.get("/game.start_cash")

        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_succesful_startcash_post(
        self, authed_cli: TestClient, store: Store
    ):
        """проверка успешности изменения данных"""

        response = await authed_cli.post(
            "/game.start_cash", json={"start_cash": 9999}
        )
        assert response.status == 200

        global_settings = await store.game.get_global_settings()

        data = await response.json()
        assert data == ok_response(
            data={"start_cash": global_settings.start_cash}
        )

    async def test_unauthorized_startcash_post(self, cli: TestClient):
        """проверка безуспешности изменения данных
        неавторизованными пользователями"""

        response = await cli.post("/game.start_cash", json={"start_cash": 9999})
        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_missed_field_startcash_post(self, authed_cli: TestClient):
        """проверка при неуказании нужного поля"""

        response = await authed_cli.post("/game.start_cash")
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert (
            data["data"]["start_cash"][0] == "Missing data for required field."
        )

    async def test_string_startcash_post(self, authed_cli: TestClient):
        """проверка при указании нужного поля с неверном типом данных"""

        response = await authed_cli.post(
            "/game.start_cash", json={"start_cash": "none"}
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Unprocessable Entity"
        assert data["data"]["start_cash"][0] == "Not a valid integer."

    async def test_zero_startcash_post(self, authed_cli: TestClient):
        """проверка при указании нужного поля со значнием ноль"""

        response = await authed_cli.post(
            "/game.start_cash", json={"start_cash": 0}
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Invalid integer"
        assert data["data"] == {}

        response = await authed_cli.post(
            "/game.start_cash", json={"start_cash": 0.2555}
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Invalid integer"
        assert data["data"] == {}

    async def test_negative_startcash_post(self, authed_cli: TestClient):
        """проверка при указании нужного поля с отрицательным значением"""
        
        response = await authed_cli.post(
            "/game.start_cash", json={"start_cash": -1000}
        )
        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Invalid integer"
        assert data["data"] == {}
