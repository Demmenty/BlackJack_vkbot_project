import typing

from store.database.database import Database

if typing.TYPE_CHECKING:
    from web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from store.admin.accessor import AdminAccessor
        from store.game.accessor import GameAccessor

        self.game = GameAccessor(app)
        self.admin = AdminAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
