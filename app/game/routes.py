import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.game.views import StartCashView

    app.router.add_view("/game.start_cash", StartCashView)
