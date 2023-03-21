from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
)

from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from store import Store, setup_store
from store.database.database import Database
from web.config import Config, setup_config
from web.logger import setup_logging


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    database: Optional[Database] = None

app = Application()


def setup_app(config_path: str) -> Application:
    setup_logging(app)
    setup_config(app, config_path)
    session_setup(app, EncryptedCookieStorage(app.config.session.key))
    setup_store(app)
    return app
