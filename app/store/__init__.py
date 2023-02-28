import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.admin.accessor import AdminAccessor
        from app.store.bot.manager import BotManager
        from app.store.game.accessor import GameAccessor
        from app.store.game.manager import GameManager
        from app.store.vk_api.accessor import VkApiAccessor

        self.game = GameAccessor(app)
        self.admin = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bot_manager = BotManager(app)
        self.game_manager = GameManager(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
