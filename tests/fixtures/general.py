import logging
import os
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import loop_context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.store import Database, Store
from app.web.app import setup_app
from app.web.config import Config

from .testclient import *


# ивентлупа
@pytest.fixture(scope="session")
def event_loop():
    with loop_context() as _loop:
        yield _loop


# создание сервера c тестовым конфигом
@pytest.fixture(scope="session")
def server():
    app = setup_app(
        config_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "config.yml"
        )
    )
    app.on_startup.clear()
    app.on_shutdown.clear()
    app.on_cleanup.clear()
    app.store.vk_api = AsyncMock()
    app.store.vk_api.send_message = AsyncMock()

    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_shutdown.append(app.database.disconnect)

    return app


# доступ к store
@pytest.fixture
def store(server) -> Store:
    return server.store


# доступ к config
@pytest.fixture
def config(server) -> Config:
    return server.config


# доступ к сессии с бд
@pytest.fixture
def db_session(server):
    return server.database.session


# !авто
# очистка бд после каждого теста
@pytest.fixture(autouse=True, scope="function")
async def clear_db(server):
    yield
    try:
        session = AsyncSession(server.database._engine)
        connection = session.connection()
        for table in server.database._db.metadata.tables:
            await session.execute(text(f"TRUNCATE {table} CASCADE"))
            await session.execute(
                text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
            )

        await session.commit()
        connection.close()

    except Exception as err:
        logging.warning(err)
