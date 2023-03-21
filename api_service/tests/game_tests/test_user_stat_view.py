from aiohttp.test_utils import TestClient

from game.models import VKUserModel
from tests.utils import ok_response


class TestUserStatView:
    async def test_unauthorized_userstat_get(self, cli: TestClient):
        """проверка безуспешности получения данных
        неавторизованным пользователем"""

        test_vk_user_id = 93683216

        response = await cli.get(
            "/user.stat", json={"user_id": test_vk_user_id}
        )

        assert response.status == 401

        data = await response.json()
        assert data["status"] == "unauthorized"
        assert data["message"] == "Unauthorized"
        assert data["data"] == {}

    async def test_succesful_userstat_2games_get(
        self, authed_cli: TestClient, vk_user_2: VKUserModel
    ):
        """проверка успешности получения статистики пользователя"""

        response = await authed_cli.get(
            "/user.stat", json={"user_id": vk_user_2.vk_id}
        )

        assert response.status == 200

        data = await response.json()
        assert data == ok_response(
            {
                "user_id": vk_user_2.vk_id,
                "number_of_gamechats": 2,
                "player_stat": [
                    {
                        "game_id": 1,
                        "games_lost": 0,
                        "games_played": 2,
                        "games_won": 1,
                    },
                    {
                        "game_id": 2,
                        "games_played": 5,
                        "games_lost": 2,
                        "games_won": 3,
                    },
                ],
            }
        )

    async def test_succesful_userstat_1game_get(
        self, authed_cli: TestClient, vk_user_3: VKUserModel
    ):
        """проверка успешности получения статистики пользователя"""

        response = await authed_cli.get(
            "/user.stat", json={"user_id": vk_user_3.vk_id}
        )

        assert response.status == 200

        data = await response.json()
        assert data == ok_response(
            {
                "user_id": vk_user_3.vk_id,
                "number_of_gamechats": 1,
                "player_stat": [
                    {
                        "game_id": 1,
                        "games_lost": 0,
                        "games_played": 2,
                        "games_won": 1,
                    }
                ],
            }
        )

    async def test_no_player_userstat_get(
        self, authed_cli: TestClient, vk_user_1: VKUserModel
    ):
        """проверка ответа на запрос статистики пользователя, не являющегося игроком"""

        response = await authed_cli.get(
            "/user.stat", json={"user_id": vk_user_1.vk_id}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "user is not registered as a player"
        assert data["data"] == {}

    async def test_wrong_method_userstat(
        self, authed_cli: TestClient, vk_user_1: VKUserModel
    ):
        """проверка ответа на неверный метод запроса"""

        response = await authed_cli.post(
            "/user.stat", json={"user_id": vk_user_1.vk_id}
        )

        assert response.status == 405
        data = await response.json()
        assert data["status"] == "not_implemented"
        assert data["message"] == "Method Not Allowed"
        assert data["data"] == {}

    async def test_invalid_data_userstat_get(self, authed_cli: TestClient):
        """проверка ответа на невалидные id"""

        int32_max = 2147483647
        int32_min = -2147483648

        response = await authed_cli.get(
            "/user.stat", json={"user_id": int32_max + 1}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "invalid user id"
        assert data["data"] == {}

        response = await authed_cli.get(
            "/user.stat", json={"user_id": int32_min - 1}
        )

        assert response.status == 404

        data = await response.json()
        assert data["status"] == "not_found"
        assert data["message"] == "invalid user id"
        assert data["data"] == {}

    async def test_missed_field_userstat_get(self, authed_cli: TestClient):
        """проверка неуспешности запроса без необходимого поля"""

        response = await authed_cli.get("/user.stat", json={})

        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Unprocessable Entity"
        assert data["data"] == {"user_id": ["Missing data for required field."]}

    async def test_string_data_userstat_get(self, authed_cli: TestClient):
        """проверка ответа на запрос с нечисловым id"""

        response = await authed_cli.get("/user.stat", json={"user_id": "test"})

        assert response.status == 400

        data = await response.json()
        assert data["status"] == "bad_request"
        assert data["message"] == "Unprocessable Entity"
        assert data["data"] == {"user_id": ["Not a valid integer."]}
