import typing
from logging import getLogger

from app.store.game.buttons import GameButton
from app.store.game.decks import EndlessDeck
from app.store.game.notifications import GameNotifier
from app.store.game.phrases import GamePhrase
from app.store.game.decorators import (
    game_must_be_off,
    game_must_be_on,
    game_must_be_on_state,
)
from app.store.vk_api.dataclasses import BotMessage, Keyboard, Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameHandler:
    """обработчик команд от участников чата"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notifier = GameNotifier(app)
        self.deck = EndlessDeck()
        self.logger = getLogger("handler")

    @game_must_be_off
    async def send_game_offer(self, update: Update) -> None:
        """отправляет предложение поиграть"""

        await self.notifier.game_offer(update.peer_id)

    @game_must_be_off
    async def start_game(self, update: Update) -> None:
        """обработка запроса на старт игры"""
        # TODO проверка наличия last_game
        # TODO нет last_game > вариант "другим составом"
        # TODO если last_game > предложить 3 варианта

        # TODO варианты:
        # "тем же составом" > define направляет в betting без waiting
        # "другим составом" > все игроки inactive > стадия define
        # "совсем заново" > все игроки inactive и cash изначальный > стадия define

        await self.app.store.game_manager.start_game(update.peer_id)

    @game_must_be_on
    @game_must_be_on_state("define_players")
    async def register_player(self, update: Update) -> None:
        """регистрирует пользователя в качестве игрока"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)

        # TODO сделать как транзакции
        vk_user = await self.app.store.game.get_or_create_vk_user(
            update.from_id
        )
        player, player_created = await self.app.store.game.get_or_create_player(
            vk_user.id, game.id
        )

        if player.cash == 0:
            await self.notifier.no_cash(update.peer_id, vk_user.name)
            return

        if player_created:
            await self.notifier.player_registered(update.peer_id, vk_user.name)
        elif player.is_active:
            await self.notifier.player_registered_already(
                update.peer_id, vk_user.name
            )
        else:
            await self.app.store.game.set_player_state(player.id, True)
            await self.notifier.player_registered(update.peer_id, vk_user.name)

    @game_must_be_on
    @game_must_be_on_state("define_players", "betting")
    async def unregister_player(self, update: Update) -> None:
        """отмечает игрока как неактивного"""
        # TODO вынести cтейты в енам, да-да

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)

        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )
        name = await self.app.store.game.get_player_name(player.id)

        if player.bet:
            await self.app.store.game.set_player_bet(player.id, None)

        await self.app.store.game.set_player_state(player.id, False)
        await self.notifier.player_unregistered(update.peer_id, name)

    @game_must_be_on
    @game_must_be_on_state("betting")
    async def accept_bet(self, update: Update) -> None:
        """проверяет и регистрирует ставку игрока"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)

        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            return

        name = await self.app.store.game.get_player_name(player.id)

        if player.bet:
            await self.notifier.bet_accepted_already(
                update.peer_id, name, player.bet
            )
            return

        # TODO вынести команды куда-то
        if update.text == "ва-банк!":
            bet = player.cash
        else:
            bet = int(update.text)

            # игроки с нулем на балансе не допускаются к игре 😎
            if bet == 0:
                await self.notifier.zero_bet(update.peer_id, name)
                return

            if bet > player.cash:
                await self.notifier.to_much_bet(update.peer_id, name)
                return

        await self.app.store.game.set_player_bet(player.id, bet)
        await self.notifier.bet_accepted(update.peer_id, name, bet)

        # TODO check: все игроки поставили -> cancel waiting_bets -> start_dealing

    @game_must_be_on
    @game_must_be_on_state("dealing")
    async def deal_more_card(self, update: Update) -> None:
        """выдает игроку еще одну карту"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            return

        if game.current_player_id != player.id:
            name = await self.app.store.game.get_player_name(player.id)
            await self.notifier.not_your_turn(update.peer_id, name)
            return

        await self.app.store.game_manager.deal_cards_to_player(
            1, update.peer_id, game.id, player.id
        )

    @game_must_be_on
    @game_must_be_on_state("dealing")
    async def stop_dealing_cards(self, update: Update) -> None:
        """останавливает раздачу карт игроку и передает ход следующему"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )

        if not player:
            return

        if game.current_player_id != player.id:
            name = await self.app.store.game.get_player_name(player.id)
            await self.notifier.not_your_turn(update.peer_id, name)
            return

        await self.app.store.game_manager.set_next_player_turn(
            update.peer_id, game.id
        )

    @game_must_be_on
    async def send_player_hand(self, update: Update) -> None:
        """отправляет в чат информацию о картах в руке игрока"""

        # TODO сделать всплывающим сообщением

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )
        if not player:
            return

        hand = player.hand["cards"]
        name = await self.app.store.game.get_player_name(player.id)
        await self.notifier.player_hand(update.peer_id, name, hand)

    async def send_player_cash(self, update: Update) -> None:
        """отправляет в чат информацию о балансе игрока, сделавшего такой запрос"""

        # TODO сделать всплывающим (sendMessageEventAnswer > show_snackbar)

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            update.from_id, game.id
        )
        name = await self.app.store.vk_api.get_username(update.from_id)

        if not player:
            await self.notifier.not_a_player(update.peer_id, name)
            return

        await self.notifier.show_cash(update.peer_id, name, player.cash)

    async def send_game_rules(self, update: Update) -> None:
        """отправляет в чат описание правил игры"""
        # TODO сделать нормальное описание правил
        # TODO чекнуть актуальность предоставляемых при этом кнопок, когда будет больше реализовано всякого
        # TODO подсказки и кнопки в зависимости от стадии игры

        msg = BotMessage(
            peer_id=update.peer_id,
            text=GamePhrase.rules,
            keyboard=Keyboard(buttons=[[GameButton.start]]).json,
        )
        await self.app.store.vk_api.send_message(msg)

    @game_must_be_on
    @game_must_be_on_state("define_players", "betting")
    async def abort_game(self, update: Update) -> None:
        """отменяет игру (никаких результатов)"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        causer = await self.app.store.vk_api.get_username(update.from_id)
        await self.app.store.game_manager.abort_game(
            update.peer_id, game.id, causer
        )

    @game_must_be_on
    @game_must_be_on_state("dealing")
    async def cancel_game(self, update: Update) -> None:
        """досрочно останавливает игру (с выводом результатов)"""

        game = await self.app.store.game.get_game_by_peer_id(update.peer_id)
        causer = await self.app.store.vk_api.get_username(update.from_id)
        await self.app.store.game_manager.stop_game(
            update.peer_id, game.id, causer
        )
