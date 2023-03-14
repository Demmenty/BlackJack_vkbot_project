from aiohttp.test_utils import TestClient
from app.store import Store
from tests.utils import ok_response


class TestChatStatView:
    async def test_unauthorized_chatstat_get(self, cli: TestClient):
        """проверка безуспешности получения данных
        неавторизованным пользователем"""

        test_vk_chat_id = 2000222222

        response = await cli.get(
            "/chat.stat", json={"chat_id": test_vk_chat_id}
        )

        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"

    async def test_succesful_chatstat_get(
        self, authed_cli: TestClient, store: Store
    ):
        """проверка успешности получения данных"""

        test_vk_chat_id = 2000222222

        chat = await store.game.create_chat(vk_id=test_vk_chat_id)

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": test_vk_chat_id}
        )

        assert response.status == 200

        data = await response.json()
        assert data == ok_response(
            {
                "chat_id": chat.vk_id,
                "games_played": chat.games_played,
                "casino_cash": chat.casino_cash,
            }
        )

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": str(test_vk_chat_id)}
        )

        assert response.status == 200

        data = await response.json()
        assert data == ok_response(
            {
                "chat_id": chat.vk_id,
                "games_played": chat.games_played,
                "casino_cash": chat.casino_cash,
            }
        )

        await store.game.add_game_played_to_chat(vk_id=test_vk_chat_id)

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": test_vk_chat_id}
        )

        assert response.status == 200

        data = await response.json()
        assert data == ok_response(
            {
                "chat_id": chat.vk_id,
                "games_played": chat.games_played + 1,
                "casino_cash": chat.casino_cash,
            }
        )

    async def test_wrong_method_chatstat(self, authed_cli: TestClient):
        """проверка ответа на неверный метод запроса"""

        test_vk_chat_id = 2000222222

        response = await authed_cli.post(
            "/chat.stat", json={"chat_id": test_vk_chat_id}
        )

        assert response.status == 405
        data = await response.json()
        assert data["status"] == "not_implemented"
        assert data["message"] == "Method Not Allowed"

    async def test_invalid_data_chatstat_get(self, authed_cli: TestClient):
        """проверка ответа на невалидные id"""

        int32_max = 2147483647
        int32_min = -2147483648

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": int32_max + 1}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "invalid chat id"
        assert data["data"] == {}

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": int32_min - 1}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "invalid chat id"
        assert data["data"] == {}

    async def test_no_chat_chatstat_get(self, authed_cli: TestClient):
        """проверка ответа на запрос несуществующего чата"""

        test_vk_chat_id = 2000222222

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": test_vk_chat_id}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "no such chat registered"
        assert data["data"] == {}

    async def test_missed_field_chatstat_get(self, authed_cli: TestClient):
        """проверка неуспешности запроса без необходимого поля"""

        response = await authed_cli.get("/chat.stat", json={})

        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Unprocessable Entity"
        assert data["data"] == {"chat_id": ["Missing data for required field."]}

    async def test_string_data_chatstat_get(self, authed_cli: TestClient):
        """проверка ответа на запрос с нечисловым id"""

        response = await authed_cli.get(
            "/chat.stat", json={"chat_id": "test_vk_chat_id"}
        )

        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Unprocessable Entity"
        assert data["data"] == {"chat_id": ["Not a valid integer."]}
