import pytest
from aiohttp.test_utils import TestClient


# !авто
# имитация клиента, выполняющего запросы
@pytest.fixture(autouse=True)
def cli(aiohttp_client, event_loop, server) -> TestClient:
    return event_loop.run_until_complete(aiohttp_client(server))


# выполнение как от авторизованного админа
@pytest.fixture
async def authed_cli(cli, config) -> TestClient:
    await cli.post(
        "/admin.login",
        data={
            "email": config.admin.email,
            "password": config.admin.password,
        },
    )
    yield cli
