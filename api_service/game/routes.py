import typing

if typing.TYPE_CHECKING:
    from web.app import Application


def setup_routes(app: "Application"):
    from game.views import ChatStatView, StartCashView, UserStatView

    app.router.add_view("/chat.stat", ChatStatView)
    app.router.add_view("/user.stat", UserStatView)
    app.router.add_view("/game.start_cash", StartCashView)
