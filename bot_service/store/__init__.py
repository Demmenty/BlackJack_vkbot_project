import typing

from store.database.database import Database

if typing.TYPE_CHECKING:
    from web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from store.bot.manager import BotManager
        from store.game.accessor import GameAccessor
        from store.game.handler import GameHandler
        from store.game.manager import GameManager
        from store.vk_api.accessor import VkApiAccessor

        self.game = GameAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.bot_manager = BotManager(app)
        self.game_manager = GameManager(app)
        self.game_handler = GameHandler(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
