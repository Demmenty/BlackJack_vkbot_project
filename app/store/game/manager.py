import typing
from asyncio import sleep as asleep
from logging import getLogger

from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

from .buttons import GameButton
from .notifications import GameNotification
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление ботом, связанное с игрой"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notify = GameNotification(app)
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
            await self.notify.that_game_is_on(peer_id=update.peer_id)
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )

        await self.notify.about_starting_of_game(peer_id=update.peer_id)
        await self.notify.about_waiting_of_players(peer_id=update.peer_id)
        await self.app.store.game.change_game_state(game.id, "waiting_players")

        await asleep(15)
        # FIXME а всмысле апдейты не присылаются во время таймера?
        # можно регистрировать timestampы и считать от них,
        # но может, я не замечаю чего-то очевидного?..

        players = await self.app.store.game.get_active_players(game_id=game.id)

        if not players:
            await self.abort_game(update)
            await self.notify.about_no_players(peer_id=update.peer_id)
            return

        # TODO уведомление с перечислением зарегистрированных игроков
        await self.manage_betting(game.id, players)

    async def register_player(self, update: Update) -> None:
        """регистрирует пользователя в качестве игрока"""

        # TODO подумать над вынесением этой проверки в декоратор -> @game_is_on
        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if not game_is_on:
            await self.notify.that_game_is_off(peer_id=update.peer_id)
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        # TODO убрать магические стринги, сделать нормально. но потом.
        if game.state != "waiting_players":
            # TODO подумать над отправкой сообщения
            return

        vk_user = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        player, player_created = await self.app.store.game.get_or_create_player(
            vk_user=vk_user, game=game
        )

        # TODO подумать, можно ли это лучше написать
        if player_created:
            await self.notify.that_player_registered(
                peer_id=update.peer_id, username=vk_user.name
            )
        elif player.is_active:
            await self.notify.that_player_registered_already(
                peer_id=update.peer_id, username=vk_user.name
            )
        else:
            await self.app.store.game.change_player_state(
                player_id=player.id, is_active=True
            )
            await self.notify.that_player_registered(
                peer_id=update.peer_id, username=vk_user.name
            )

    async def unregister_player(self, update: Update) -> None:
        """отмечает игрока как неактивного"""
        # TODO вынести cтейты в енам, да-да

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        if not game or game.state != "waiting_players":
            return

        vk_user = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        player, is_created = await self.app.store.game.get_or_create_player(
            vk_user=vk_user, game=game
        )
        await self.app.store.game.change_player_state(
            player_id=player.id, is_active=False
        )
        await self.notify.that_player_unregistered(
            peer_id=update.peer_id, username=vk_user.name
        )

    async def manage_betting(self, game_id: int, players: list) -> None:
        """стадия ставок"""

        raise NotImplementedError

    async def send_game_rules(self, update: Update) -> None:
        """описание правил игры"""
        # TODO сделать нормальное описание правил

        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.rules,
            keyboard=Keyboard(buttons=[[GameButton.start]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    async def abort_game(self, update: Update) -> None:
        """отменяет игру, если идет набор игроков"""

        # TODO убрать магические стринги и cтейты вынести в енам (потом, пока так)

        game = await self.app.store.game.get_game_by_chat(
            chat_id=update.peer_id
        )

        if not game or game.state == "inactive":
            await self.notify.that_game_is_off(peer_id=update.peer_id)
            return

        if game.state == "waiting_players":
            # TODO убрать игроков
            await self.app.store.game.change_game_state(game.id, "inactive")
            await self.notify.that_game_aborted(peer_id=update.peer_id)

    async def cancel_game(self, update: Update) -> None:
        """досрочно останавливает игру"""

        # TODO убрать магические стринги и cтейты вынести в енам (потом, пока так)

        game = await self.app.store.game.get_game_by_chat(
            chat_id=update.peer_id
        )
        if not game or game.state == "inactive":
            await self.notify.that_game_is_off(peer_id=update.peer_id)
            return

        # TODO удалить игроков
        # TODO собрать и показать какие-то результаты
        await self.app.store.game.change_game_state(game.id, "inactive")

        causer = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        await self.notify.that_game_canceled(
            peer_id=update.peer_id, username=causer.name
        )
