import typing
from logging import getLogger

from app.game.states import GameState
from app.store.game.decks import EndlessDeck
from app.store.game.decorators import (
    game_must_be_off,
    game_must_be_on,
    game_must_be_on_state,
)
from app.store.game.events import GameEvent
from app.store.game.notifications import GameNotifier
from app.store.game.phrases import GamePhrase
from app.store.vk_api.dataclasses import BotMessage, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameHandler:
    """обработчик команд от участников чата"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notifier = GameNotifier(app)
        self.deck = EndlessDeck()
        self.logger = getLogger("game handler")

    @game_must_be_off
    async def send_game_offer(self, update: Update) -> None:
        """отправляет предложение поиграть"""

        chat = await self.app.store.game.get_chat_by_vk_id(update.peer_id)
        if chat and chat.games_played:
            await self.notifier.game_offer(update.peer_id, again=True)
        else:
            await self.notifier.game_offer(update.peer_id)

    @game_must_be_off
    async def start_game(self, update: Update) -> None:
        """обработка запроса на старт игры"""

        chat = await self.app.store.game.get_chat_by_vk_id(update.peer_id)

        if not chat:
            chat = await self.app.store.game.create_chat(update.peer_id)
            game = await self.app.store.game.create_game(chat.id)
        else:
            game = await self.app.store.game.get_game_by_chat_id(chat.id)

        chat_users = await self.app.store.vk_api.get_chat_users(update.peer_id)

        if chat_users:
            num_of_losers = await self.app.store.game.count_losers(game.id)
            if len(chat_users) == num_of_losers:
                await self.notifier.all_losers(update.peer_id)
                return

        await self.app.store.game_manager.start_game(update.peer_id, game.id)

    @game_must_be_on
    @game_must_be_on_state(GameState.gathering)
    async def register_player(self, update: Update) -> None:
        """регистрирует пользователя в качестве игрока"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)

        # TODO сделать как транзакции
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            vk_user = await self.app.store.game.get_vk_user_by_vk_id(
                update.from_id
            )
            if not vk_user:
                vk_user = await self.app.store.game.create_vk_user(
                    update.from_id
                )

            player = await self.app.store.game.create_player(
                vk_user.id, game.id
            )
            await self.notifier.start_cash_given(update.peer_id, vk_user.name)

        else:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)

            if player.cash == 0:
                await self.notifier.no_cash_to_play(
                    update.peer_id, vk_user.name
                )
                return

            if player.is_active:
                await self.notifier.player_registered_already(
                    update.peer_id, vk_user.name
                )
                return

            await self.app.store.game.set_player_state(player.id, True)

        await self.notifier.player_registered(update.peer_id, vk_user.name)

        losers = await self.app.store.game.count_losers(game.id)
        all_play = await self._is_all_play(update.peer_id, game.id, losers)

        if all_play:
            await self.app.store.game_manager.timer.end_timer(game.id)
            await self.notifier.all_play(update.peer_id, losers)
            await self.app.store.game_manager.start_betting(
                update.peer_id, game.id
            )

    async def _is_all_play(
        self, vk_chat_id: int, game_id: int, losers: int
    ) -> bool:
        """предикат, проверяющий, все ли участники чата,
        у которых остался cash, согласились играть"""
        # TODO учитывать нажавших "пас"
        chat_users = await self.app.store.vk_api.get_chat_users(vk_chat_id)
        if not chat_users:
            return False

        active_players = await self.app.store.game.get_active_players(game_id)
        if not active_players:
            return False

        return len(active_players) == (len(chat_users) - losers)

    @game_must_be_on
    @game_must_be_on_state(GameState.gathering, GameState.betting)
    async def unregister_player(self, update: Update) -> None:
        """отмечает игрока как неактивного"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)

        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            await self.notifier.player_unregistered(
                update.peer_id, vk_user.name
            )
            return

        if player.bet:
            await self.app.store.game.set_player_bet(player.id, None)

        await self.app.store.game.set_player_state(player.id, False)

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_unregistered(update.peer_id, vk_user.name)

    @game_must_be_on
    @game_must_be_on_state(GameState.betting)
    async def accept_bet(self, update: Update) -> None:
        """проверяет и регистрирует ставку игрока"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player or not player.is_active:
            return

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)

        if player.bet:
            await self.notifier.bet_accepted_already(
                update.peer_id, vk_user.name, player.bet, vk_user.sex
            )
            return

        if update.text == GameEvent.bet.value:
            bet = player.cash
        else:
            bet = int(update.text)

            if bet == 0:
                await self.notifier.zero_bet(update.peer_id, vk_user.name)
                return

            if bet > player.cash:
                await self.notifier.to_much_bet(update.peer_id, vk_user.name)
                return

        await self.app.store.game.set_player_bet(player.id, bet)
        await self.notifier.bet_accepted(update.peer_id, vk_user.name, bet)

        active_players = await self.app.store.game.get_active_players(game.id)

        if all(player.bet for player in active_players):
            await self.app.store.game_manager.timer.end_timer(game.id)
            await self.notifier.all_bets_placed(update.peer_id)
            await self.app.store.game_manager.start_dealing(
                update.peer_id, game.id
            )

    @game_must_be_on
    @game_must_be_on_state(GameState.dealing_players)
    async def deal_more_card(self, update: Update) -> None:
        """останавливает таймер и выдает игроку еще одну карту"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            await self.notifier.not_a_player(update.peer_id, vk_user.name)
            return

        if game.current_player_id != player.id:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            await self.notifier.not_your_turn(update.peer_id, vk_user.name)
            return

        await self.app.store.game_manager.timer.end_timer(game.id)
        await self.app.store.game_manager.deal_cards_to_player(
            1, update.peer_id, game.id, player.id
        )

    @game_must_be_on
    @game_must_be_on_state(GameState.dealing_players)
    async def stop_dealing_cards(self, update: Update) -> None:
        """останавливает раздачу карт игроку,
        останавливает таймер и передает ход следующему"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            await self.notifier.not_a_player(update.peer_id, vk_user.name)
            return

        if game.current_player_id != player.id:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            await self.notifier.not_your_turn(update.peer_id, vk_user.name)
            return

        await self.app.store.game_manager.timer.end_timer(game.id)
        await self.app.store.game_manager.set_next_player_turn(
            update.peer_id, game.id
        )

    @game_must_be_on
    async def send_player_hand(self, update: Update) -> None:
        """отправляет в чат информацию о картах в руке игрока"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )
        if not player:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            hand = []
        else:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            hand = player.hand["cards"]

        await self.notifier.player_hand(update.peer_id, vk_user.name, hand)

    async def send_player_cash(self, update: Update) -> None:
        """отправляет в чат информацию о балансе игрока, сделавшего такой запрос"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            await self.notifier.not_a_player_cash(update.peer_id, vk_user.name)
            return

        if player.bet:
            player.cash -= player.bet

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.show_cash(update.peer_id, vk_user.name, player.cash)

    async def send_game_rules(self, update: Update) -> None:
        """отправляет в чат описание правил игры"""

        vk_user = await self.app.store.vk_api.get_user(update.from_id)
        msg = BotMessage(
            peer_id=update.peer_id, text=GamePhrase.rules(vk_user.name)
        )
        await self.app.store.vk_api.send_message(msg)

    @game_must_be_on
    @game_must_be_on_state(GameState.gathering, GameState.betting)
    async def abort_game(self, update: Update) -> None:
        """отменяет игру"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        await self.app.store.game_manager.inactivate_game(game.id)

        causer = await self.app.store.vk_api.get_user(update.from_id)
        await self.notifier.game_aborted(update.peer_id, causer.name)

    @game_must_be_on
    @game_must_be_on_state(
        GameState.dealing_players, GameState.dealing_dealer, GameState.results
    )
    async def cancel_game(self, update: Update) -> None:
        """досрочно останавливает игру"""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        await self.app.store.game_manager.inactivate_game(game.id)

        causer = await self.app.store.vk_api.get_user(update.from_id)
        await self.notifier.game_canceled(update.peer_id, causer.name)

    async def send_statistic(self, update: Update) -> None:
        """обрабатывает запрос статистики"""

        await self.app.store.game_manager.send_statistic(
            update.peer_id, update.from_id
        )

    async def send_restore_command(self, update: Update) -> None:
        """отправляет команду для восстановления cash у всех игроков.
        но только если есть хотя бы один проигравшийся."""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        losers = await self.app.store.game.count_losers(game.id)

        if losers:
            vk_user = await self.app.store.vk_api.get_user(update.from_id)
            await self.notifier.restore_command(
                update.peer_id, vk_user.name, vk_user.sex
            )

    async def restore_game_and_cash(self, update: Update) -> None:
        """инактивирует игру и делает cash игроков стартовым.
        но только если есть хотя бы один проигравшийся."""

        game = await self.app.store.game.get_game_by_vk_id(update.peer_id)
        losers = await self.app.store.game.count_losers(game.id)

        if not losers:
            return

        await self.app.store.game_manager.inactivate_game(game.id)

        players = await self.app.store.game.get_players(game.id)
        global_settings = await self.app.store.game.get_global_settings()
        for player in players:
            await self.app.store.game.set_player_cash(
                player.id, new_cash=global_settings.start_cash
            )

        await self.notifier.cash_restored(update.peer_id)
        await self.notifier.game_offer(update.peer_id)
