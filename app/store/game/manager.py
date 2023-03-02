import typing
from asyncio import sleep as asleep
from logging import getLogger

from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

from .buttons import GameButton
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление ботом, связанное с игрой"""

    def __init__(self, app: "Application"):
        self.app = app
        self.logger = getLogger("handler")

    async def offer_game(self, update: Update) -> None:
        """отправляет в беседу предложение поиграть"""

        # TODO проверка, если в беседе уже была игра -> статистика
        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )

        if not game_is_on:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_offer,
                keyboard=Keyboard(
                    buttons=[[GameButton.start, GameButton.rules]]
                ).json,
            )
            await self.app.store.vk_api.send_message(msg)

    async def start_new_game(self, update: Update) -> None:
        """начало новой игры"""

        # TODO кнопка отказа, чтобы не ждать: сделать админом > получить участников чата > сравнить

        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if game_is_on:
            await self._notify_that_game_is_on(peer_id=update.peer_id)
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )

        await self._notify_about_starting_of_game(peer_id=update.peer_id)
        await self._notify_about_waiting_of_players(peer_id=update.peer_id)
        await self.app.store.game.change_game_state(game.id, "waiting_players")

        await asleep(15)

        players = await self.app.store.game.get_all_players(game_id=game.id)

        if not players:
            await self.cancel_game(update)
            await self._notify_about_no_players(peer_id=update.peer_id)
            return

        await self.manage_betting(game.id, players)

    # TODO сделать отдельный класс GameNotification...
    async def _notify_that_game_is_on(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра уже идет"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_is_on,
        )
        await self.app.store.vk_api.send_message(msg)

    async def _notify_that_game_is_off(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра сейчас не идет"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_is_off,
        )
        await self.app.store.vk_api.send_message(msg)

    async def _notify_that_game_aborted(self, peer_id: int) -> None:
        """уведомляет чат о том, что игра отменена"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_abort,
        )
        await self.app.store.vk_api.send_message(msg)

    async def _notify_about_starting_of_game(self, peer_id: int) -> None:
        """уведомляет чат о начале игры"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.game_begun,
        )
        await self.app.store.vk_api.send_message(msg)

    async def _notify_about_waiting_of_players(self, peer_id: int) -> None:
        """уведомляет чат о начале набора игроков"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.wait_players,
            keyboard=Keyboard(
                buttons=[[GameButton.acceptgame, GameButton.abort]]
            ).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def _notify_about_no_players(self, peer_id: int) -> None:
        """уведомляет чат о том, что они петухи"""

        msg = BotMessage(
            peer_id=peer_id,
            text=GamePhrase.no_players,
        )
        await self.app.store.vk_api.send_message(msg)

    async def register_player(self, update: Update) -> None:
        """регистрирует пользователя в качестве игрока"""

        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if not game_is_on:
            # TODO подумать над отправкой сообщения
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        # TODO убрать магические стринги, сделать нормально. но потом.
        if game.state != "waiting_players":
            # TODO подумать над отправкой сообщения
            return

        # TODO отрегулировать, чтобы один и тот же не создавался
        vk_user = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        player = await self.app.store.game.create_player(
            vk_user=vk_user, game=game
        )

        # TODO проверить на работоспособность после слияния!
        msg = BotMessage(
            peer_id=update.peer_id,
            text=vk_user.name + GamePhrase.player_registered,
        )
        await self.app.store.vk_api.send_message(msg)

    async def manage_betting(self, game_id: int, players: list) -> None:
        """стадия ставок"""

        # TODO раздать всем деняк

        raise NotImplementedError

    async def send_game_rules(self, update: Update) -> None:
        """описание правил игры"""

        # TODO проверить статус игры -> отправлять кнопку только если "inactive"

        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.rules,
            keyboard=Keyboard(buttons=[[GameButton.start]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def cancel_game(self, update: Update) -> None:
        """останавливает игру"""

        # TODO убрать магические стринги и cтейты вынести в енам (потом, пока так)
        # TODO проработать остальные варианты в зависимости от state (вывести результаты)
        # TODO подумать над резделением методов на abort и end

        game = await self.app.store.game.get_game_by_chat(
            chat_id=update.peer_id
        )
        # чекнуть, что так не ломается если game is None
        if not game or game.state == "inactive":
            await self._notify_that_game_is_off(peer_id=update.peer_id)
            return

        if game.state == "waiting_players":
            # TODO удалить игроков
            await self.app.store.game.change_game_state(game.id, "inactive")
            await self._notify_that_game_aborted(peer_id=update.peer_id)
