from store import Store


class TestGlobalSettings:
    async def test_global_settings_created_on_startapp(self, store: Store):
        """проверка факта создания записи глобальных настроек при запуске
        с валидными параметрами"""

        global_settings = await store.game.get_global_settings()

        assert global_settings is not None
        assert global_settings.start_cash is not None
        assert global_settings.start_cash > 0
        assert global_settings.id == 1
