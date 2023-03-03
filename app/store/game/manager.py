import typing
from asyncio import create_task, sleep as asleep
from logging import getLogger

from app.game.models import PlayerModel
from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

from .buttons import GameButton
from .notifications import GameNotifier
from .phrases import GamePhrase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление ботом, связанное с игрой"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notifier = GameNotifier(app)
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
        """обработка запроса на старт игры"""
        # TODO проверка наличия last_game
        # TODO нет last_game > вариант "другим составом"
        # TODO если last_game > предложить 3 варианта

        # TODO сделать эту проверку декоратором, наверное
        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if game_is_on:
            await self.notifier.game_is_on(peer_id=update.peer_id)
            return

        await self.notifier.game_starting(peer_id=update.peer_id)

        # TODO варианты:
        # "тем же составом" > define направляет в betting без waiting
        # "другим составом" > все игроки inactive > стадия define
        # "совсем заново" > все игроки inactive и cash изначальный > стадия define

        await self.define_players(update)

    async def define_players(self, update: Update) -> None:
        """стадия определения игроков раунда"""

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        await self.app.store.game.change_game_state(game.id, "define_players")

        await self.notifier.waiting_players(peer_id=update.peer_id)

        create_task(self.waiting_players(game.id, update))
        # TODO организовать какой-то там коллбек

    async def waiting_players(self, game_id: int, update: Update) -> None:
        """ждет, пока отметятся игроки, собирает их и направляет на стадию ставок"""

        await asleep(15)

        players = await self.app.store.game.get_active_players(game_id=game_id)

        if not players:
            await self.abort_game(update)
            await self.notifier.no_players(peer_id=update.peer_id)
            return

        players_names: list[str] = [
            await self.app.store.game.get_player_name(player.id)
            for player in players
        ]
        await self.notifier.active_players(
            peer_id=update.peer_id, names=players_names
        )
        await self.manage_betting(update.peer_id, game_id, players)

    async def register_player(self, update: Update) -> None:
        """регистрирует пользователя в качестве игрока"""

        # TODO подумать над вынесением этой проверки в декоратор -> @game_is_on
        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if not game_is_on:
            await self.notifier.game_is_off(peer_id=update.peer_id)
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        # TODO убрать магические стринги, сделать нормально. но потом.
        if game.state != "define_players":
            # TODO подумать над отправкой сообщения
            return

        # TODO сделать как транзакции
        vk_user = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        player, player_created = await self.app.store.game.get_or_create_player(
            vk_user=vk_user, game=game
        )

        if player.cash == 0:
            await self.app.store.game.change_player_state(
                player_id=player.id, is_active=False
            )
            await self.notifier.no_cash(
                peer_id=update.peer_id, username=vk_user.name
            )
            return

        if player_created:
            await self.notifier.player_registered(
                peer_id=update.peer_id, username=vk_user.name
            )
        elif player.is_active:
            await self.notifier.player_registered_already(
                peer_id=update.peer_id, username=vk_user.name
            )
        else:
            await self.app.store.game.change_player_state(
                player_id=player.id, is_active=True
            )
            await self.notifier.player_registered(
                peer_id=update.peer_id, username=vk_user.name
            )

    async def unregister_player(self, update: Update) -> None:
        """отмечает игрока как неактивного"""
        # TODO вынести cтейты в енам, да-да

        # TODO декоратор с подстановкой нужной стадии типа @game_state(state)
        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )
        # TODO выйти из игры во время ставок
        if not game or game.state != "define_players":
            return

        # TODO сделать следующее как транзакция (вся функция)
        vk_user = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        player, is_created = await self.app.store.game.get_or_create_player(
            vk_user=vk_user, game=game
        )
        await self.app.store.game.change_player_state(
            player_id=player.id, is_active=False
        )
        await self.notifier.player_unregistered(
            peer_id=update.peer_id, username=vk_user.name
        )

    async def manage_betting(
        self, peer_id: int, game_id: int, players: list
    ) -> None:
        """стадия ставок"""

        await self.app.store.game.change_game_state(game_id, "betting")
        await self.notifier.wait_bets(peer_id=peer_id)

        create_task(self.waiting_bets(peer_id, game_id, players))
        # TODO организовать какой-то там коллбек

    async def waiting_bets(
        self, peer_id: int, game_id: int, players: list[PlayerModel]
    ) -> None:
        """ждет, пока игроки не сделают ставки и направляет на след. стадию"""

        await asleep(30)

        players = await self.app.store.game.get_active_players(game_id)
        # TODO if not players ...

        bets_are_made = True
        for player in players:
            if player.bet is None:
                bets_are_made = False
                username = await self.app.store.game.get_player_name(player.id)
                await self.notifier.no_bet(peer_id, username)

        if not bets_are_made:
            create_task(self.waiting_bets(peer_id, game_id, players))
            return

        await self.manage_dealing(peer_id, game_id, players)

    async def accept_bet(self, update: Update) -> None:
        """проверяет и регистрирует ставку игрока"""
        # TODO декоратор на проверку нужной стадии
        game_is_on = await self.app.store.game.is_game_on(
            chat_id=update.peer_id
        )
        if not game_is_on:
            await self.notifier.game_is_off(peer_id=update.peer_id)
            return

        game = await self.app.store.game.get_or_create_game(
            chat_id=update.peer_id
        )

        if game.state != "betting":
            return

        player = await self.app.store.game.get_player(
            vk_user_id=update.from_id, game_id=game.id
        )
        if not player:
            return

        bet = int(update.text)
        username = await self.app.store.game.get_player_name(player.id)

        if bet == 0:
            await self.notifier.zero_bet(
                peer_id=update.peer_id, username=username
            )
            return

        if player.bet is not None:
            await self.notifier.bet_accepted_already(
                peer_id=update.peer_id, username=username, bet=player.bet
            )
            return

        if bet > player.cash:
            await self.notifier.to_much_bet(
                peer_id=update.peer_id, username=username
            )
            return

        await self.app.store.game.change_player_bet(
            player_id=player.id, new_bet=bet
        )
        await self.notifier.bet_accepted(
            peer_id=update.peer_id, username=username, bet=bet
        )

    async def send_player_cash(self, update: Update) -> None:
        """отправляет в чат информацию о балансе игрока, сделавшего такой запрос"""
        # TODO сделать всплывающим (sendMessageEventAnswer > show_snackbar)

        game = await self.app.store.game.get_game_by_chat(
            chat_id=update.peer_id
        )
        player = await self.app.store.game.get_player(
            vk_user_id=update.from_id, game_id=game.id
        )
        name = await self.app.store.vk_api.get_username(
            vk_user_id=update.from_id
        )

        if not player:
            msg = BotMessage(
                peer_id=update.peer_id,
                text=name + GamePhrase.not_a_player,
            )
            await self.app.store.vk_api.send_message(msg)
            return

        msg = BotMessage(
            peer_id=update.peer_id,
            text=name + GamePhrase.show_cash + str(player.cash),
        )
        await self.app.store.vk_api.send_message(msg)

    async def send_game_rules(self, update: Update) -> None:
        """описание правил игры"""
        # TODO сделать нормальное описание правил
        # TODO чекнуть актуальность предоставляемых при этом кнопок, когда будет больше реализовано всякого

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
            await self.notifier.game_is_off(peer_id=update.peer_id)
            return

        if game.state == "define_players" or game.state == "betting":
            players = await self.app.store.game.get_active_players(game.id)
            for player in players:
                await self.app.store.game.change_player_state(
                    player_id=player.id, is_active=False
                )
                await self.app.store.game.change_player_bet(
                    player_id=player.id, new_bet=None
                )

            await self.app.store.game.change_game_state(game.id, "inactive")
            await self.notifier.game_aborted(peer_id=update.peer_id)

    async def cancel_game(self, update: Update) -> None:
        """досрочно останавливает игру"""

        # TODO убрать магические стринги и cтейты вынести в енам (потом, пока так)

        game = await self.app.store.game.get_game_by_chat(
            chat_id=update.peer_id
        )
        if not game or game.state == "inactive":
            await self.notifier.game_is_off(peer_id=update.peer_id)
            return

        # TODO удалить игроков
        # TODO собрать и показать какие-то результаты
        await self.app.store.game.change_game_state(game.id, "inactive")

        causer = await self.app.store.game.get_or_create_vk_user(
            vk_user_id=update.from_id
        )
        await self.notifier.game_canceled(
            peer_id=update.peer_id, username=causer.name
        )
