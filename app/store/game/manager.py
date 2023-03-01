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
        game_is_on = await self.app.store.game.is_game_on(chat_id=update.peer_id)

        if not game_is_on:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_offer,
                keyboard=Keyboard(buttons=[[GameButton.start, GameButton.rules]]).json,
            )
            await self.app.store.vk_api.send_message(msg)

    async def start_new_game(self, update: Update) -> None:
        """начало новой игры"""

        # проверяем, идет ли уже игра в этом чате
        game_is_on = await self.app.store.game.is_game_on(chat_id=update.peer_id)
        # если идет, отправляем соотв.сообщение
        if game_is_on:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_is_on,
            )
            await self.app.store.vk_api.send_message(msg)
            return
        # если не идет - получаем ее модель
        game = await self.app.store.game.get_or_create_game(chat_id=update.peer_id)
        # информируем чат, что игра пошла
        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.game_begun,
        )
        await self.app.store.vk_api.send_message(msg)

        # TODO кнопка отказа, чтобы не ждать:
        # просьба сделать админом -> получить участников беседы -> сравнить

        # информируем чат о наборе игроков
        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.wait_players,
            keyboard=Keyboard(buttons=[[GameButton.acceptgame, GameButton.abort]]).json,
        )
        await self.app.store.vk_api.send_message(msg)
        # переводим игру в следующее состояние
        await self.app.store.game.change_game_state(game.id, "define_players")
        # ждем 15 секунд
        await asleep(15)
        # чекаем игроков, успевших зарегаться на игру
        players = await self.app.store.game.get_all_players(game_id=game.id)
        # проверяем, что есть хотя бы один
        if not players:
            await self.app.store.game.change_game_state(game.id, "inactive")
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.no_players,
            )
            await self.app.store.vk_api.send_message(msg)
            return
        # передаем управление обработчику следующей стадии
        await self.manage_betting(game.id, players)
        
    async def register_player(self, update: Update) -> None:
        """регистрируем пользователя в игре"""

        # статус игры должен быть "define_players"
        # проверяем, идет ли вообще игра в этом чате
        game_is_on = await self.app.store.game.is_game_on(chat_id=update.peer_id)
        if not game_is_on:
            # TODO подумать над отправкой сообщения
            return
        
        game = self.app.store.game.get_or_create_game(chat_id=update.peer_id)
        # TODO убрать магические стринги, сделать нормально. но потом.
        if game.state != "define_players":
            # TODO подумать над отправкой сообщения
            return
        
        # создаем игрока в базе
        vk_user = await self.app.store.game.get_or_create_vk_user(vk_user_id=update.from_id)
        player = await self.app.store.game.create_player(vk_user=vk_user, game=game)

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
        """заканчивает активную игру в чате переданного update"""
        # TODO убрать магические стринги и сделать чисто (потом, пока так)
        # TODO проработать все варианты в зависимости от state

        game = await self.app.store.game.get_game_by_chat(chat_id=update.peer_id)

        if not game:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_is_off,
            )
            await self.app.store.vk_api.send_message(msg)
            return

        if game.state == "inactive":
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_is_off,
            )
            await self.app.store.vk_api.send_message(msg)
            return

        if game.state == "define_players":
            await self.app.store.game.change_game_state(game.id, "inactive")
            msg = BotMessage(
                peer_id=update.peer_id,
                text=GamePhrase.game_abort,
            )
            await self.app.store.vk_api.send_message(msg)
