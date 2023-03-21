import typing

if typing.TYPE_CHECKING:
    from web.app import Application


def setup_routes(app: "Application"):
    from admin.views import AdminLoginView
    from admin.views import AdminCurrentView

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
