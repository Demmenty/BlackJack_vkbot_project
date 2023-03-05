from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.store.database import db

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None

    async def connect(self, *_: Any, **__: Any) -> None:
        self._db = db

        url = (
            "postgresql+asyncpg://"
            + str(self.app.config.database.user)
            + ":"
            + str(self.app.config.database.password)
            + "@"
            + str(self.app.config.database.host)
            + ":"
            + str(self.app.config.database.port)
            + "/"
            + str(self.app.config.database.database)
        )

        self._engine = create_async_engine(url, echo=True, future=True)

        self.session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

        await self.app.store.admin.create_admin(
            email=self.app.config.admin.email,
            password=self.app.config.admin.password,
        )

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self._engine:
            await self._engine.dispose()
