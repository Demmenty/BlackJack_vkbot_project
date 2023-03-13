import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.game.views import ChatStatView, UserStatView

    app.router.add_view("/game.stat", ChatStatView)
    app.router.add_view("/user.stat", UserStatView)
