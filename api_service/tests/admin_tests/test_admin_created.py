from hashlib import sha256

from store import Store
from web.config import Config


class TestAdminCreated:
    async def test_admin_created_on_startup(self, store: Store, config: Config):
        """проверка, что админ создан при запуске с настройками из конфига"""

        admin = await store.admin.get_by_email(config.admin.email)

        assert admin is not None
        assert admin.email == config.admin.email
        assert admin.id == 1

    async def test_admin_hashed_password(self, store: Store, config: Config):
        """проверка, что пароль созданного при запуске админа захеширован"""

        admin = await store.admin.get_by_email(config.admin.email)

        assert admin.password != config.admin.password
        assert (
            admin.password == sha256(config.admin.password.encode()).hexdigest()
        )
