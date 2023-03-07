import random
import typing
from asyncio import create_task, sleep as asleep
from logging import getLogger

from app.store.game.decks import EndlessDeck
from app.store.game.notifications import GameNotifier

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление процессом игры"""

    def __init__(self, app: "Application"):
        self.app = app
        self.notifier = GameNotifier(app)
        self.deck = EndlessDeck()
        self.logger = getLogger("handler")

    async def start_game(self, vk_id: int) -> None:
        """запускает новую игру, направляет на стадию сбора игроков"""

        chat = await self.app.store.game.get_chat_by_vk_id(vk_id)
        if not chat:
            chat = await self.app.store.game.create_chat(vk_id)
            game = await self.app.store.game.create_game(chat.id)
        else:
            game = await self.app.store.game.get_game_by_chat_id(chat.id)

        await self.notifier.game_starting(vk_id)

        await self.define_players(vk_id, game.id)

    async def define_players(
        self,
        vk_id: int,
        game_id: int,
    ) -> None:
        """запускает ожидание игроков"""

        await self.app.store.game.set_game_state(game_id, "define_players")
        await self.notifier.waiting_players(vk_id)

        create_task(self._waiting_players(vk_id, game_id))
        # TODO организовать какой-то там коллбек

    async def _waiting_players(self, vk_id: int, game_id: int) -> None:
        """ждет, пока отметятся игроки,
        тогда направляет на стадию ставок"""

        await asleep(15)

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.notifier.no_players(vk_id)
            await self.abort_game(vk_id, game_id)
            return

        players_names: list[str] = []
        for player in players:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            players_names.append(vk_user.name)

        await self.notifier.active_players(vk_id, players_names)
        await self.start_betting(vk_id, game_id)

    async def start_betting(self, vk_id: int, game_id: int) -> None:
        """запускает ожидание ставок"""

        await self.app.store.game.set_game_state(game_id, "betting")
        await self.notifier.waiting_bets(vk_id)

        create_task(self.waiting_bets(vk_id, game_id))
        # TODO организовать какой-то там коллбек

    async def waiting_bets(self, vk_id: int, game_id: int) -> None:
        """ждет, пока игроки не сделают ставки,
        тогда направляет на стадию раздачи карт"""
        # TODO поставить таймеры побольше + отменять их, если всех дождались
        await asleep(30)

        players = await self.app.store.game.get_active_players(game_id)

        for player in players:
            if player.bet is None:
                vk_user = await self.app.store.game.get_vk_user_by_player(
                    player.id
                )
                await self.app.store.game.set_player_state(player.id, False)
                await self.notifier.no_player_bet(vk_id, vk_user.name)

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.notifier.no_players(vk_id)
            await self.abort_game(vk_id, game_id)
            return

        await self.start_dealing(vk_id, game_id)

    async def start_dealing(self, vk_id: int, game_id: int) -> None:
        """запускает стадию раздачи карт"""

        await self.app.store.game.set_game_state(game_id, "dealing")
        await self.notifier.dealing_started(vk_id)

        players = await self.app.store.game.get_active_players(game_id)

        # TODO возможно, убрать показ игроков тут, подумать
        # TODO показывать игроков тут, если изменились
        # players_names: list[str] = []
        # for player in players:
        #     vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        #     players_names.append(vk_user.name)

        # TODO транзакции
        player = random.choice(players)

        await self.app.store.game.set_current_player(player.id, game_id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_turn(vk_id, vk_user.name, vk_user.sex)

        await self.deal_cards_to_player(2, vk_id, game_id, player.id)
        await self.app.store.game.add_game_played_to_chat(vk_id)

    async def deal_cards_to_player(
        self, amount: int, vk_id: int, game_id: int, player_id: int
    ) -> None:
        """выдает игроку карты в указанном количестве"""

        cards = [self.deck.take_a_card() for card in range(amount)]

        await self.app.store.game.add_cards_to_player(player_id, cards)
        await self.notifier.cards_received(vk_id, cards)

        await self._check_player_hand(vk_id, game_id, player_id)

    async def _check_player_hand(
        self, vk_id: int, game_id: int, player_id: int
    ) -> None:
        """проверяет сумму карт в руке игрока и делает выводы"""

        player = await self.app.store.game.get_player_by_id(player_id)
        player_cards = player.hand["cards"]
        player_points = self.deck.count_points(player_cards)

        if player_points == 21:
            if len(player_cards) == 2:
                vk_user = await self.app.store.game.get_vk_user_by_player(
                    player.id
                )
                await self.notifier.player_blackjack(vk_id, vk_user.name)
            await self.set_next_player_turn(vk_id, game_id)
            return

        if player_points > 21:
            await self.notifier.player_overflow(vk_id)
            await self.set_player_loss(vk_id, player_id)
            await self.set_next_player_turn(vk_id, game_id)
            return

        if player_points < 21:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            await self.notifier.offer_a_card(vk_id, vk_user.name)
            create_task(self._waiting_player_turn(vk_id, game_id, player.id))

    async def _waiting_player_turn(
        self, vk_id: int, game_id: int, player_id: int
    ) -> None:
        """ждет, пока игрок примет решение, брать еще карту или остановиться.
        таймер вышел = остановиться"""
        # TODO отменять таймер, если походил
        player = await self.app.store.game.get_player_by_id(player_id)
        start_card_amount = len(player.hand["cards"])

        await asleep(30)

        game = await self.app.store.game.get_game_by_id(game_id)
        player = await self.app.store.game.get_player_by_id(player_id)
        curr_card_amount = len(player.hand["cards"])

        if (
            curr_card_amount == start_card_amount
            and game.current_player_id == True
        ):
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            await self.notifier.no_player_card_move(
                vk_id, vk_user.name, vk_user.sex
            )
            await self.set_next_player_turn(vk_id, game.id)

    async def set_next_player_turn(self, vk_id: int, game_id: int) -> None:
        """запускает раздачу карт следующему игроку"""

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.end_game(vk_id, game_id)
            return

        players_without_cards = [
            player for player in players if not player.hand["cards"]
        ]

        if not players_without_cards:
            await self.deal_to_dealer(vk_id, game_id)
            return

        player = random.choice(players_without_cards)

        await self.app.store.game.set_current_player(player.id, game_id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_turn(vk_id, vk_user.name, vk_user.sex)

        await self.deal_cards_to_player(2, vk_id, game_id, player.id)

    async def deal_to_dealer(self, vk_id: int, game_id: int) -> None:
        """запускает раздачу карты дилеру"""

        await self.notifier.deal_to_dealer(vk_id)

        dealer_cards = [self.deck.take_a_card(), self.deck.take_a_card()]
        dealer_points = self.deck.count_points(dealer_cards)

        while dealer_points < 17:
            dealer_cards.append(self.deck.take_a_card())
            dealer_points = self.deck.count_points(dealer_cards)

        await self.app.store.game.set_dealer_points(game_id, dealer_points)
        await self.notifier.cards_received(vk_id, dealer_cards)

        await self.sum_up_results(vk_id, game_id)

    async def sum_up_results(self, vk_id: int, game_id: int) -> None:
        """сравнивает очки оставшихся игроков и дилера, подводя итоги"""

        players = await self.app.store.game.get_active_players(game_id)
        dealer_points = await self.app.store.game.get_dealer_points(game_id)

        if dealer_points > 21:
            for player in players:
                if self.deck.is_blackjack(player.hand["cards"]):
                    await self.set_player_win(vk_id, player.id, blackjack=True)
                else:
                    await self.set_player_win(vk_id, player.id)
        else:
            for player in players:
                player_points = self.deck.count_points(player.hand["cards"])

                if (
                    self.deck.is_blackjack(player.hand["cards"])
                    and dealer_points < 21
                ):
                    await self.set_player_win(vk_id, player.id, blackjack=True)
                elif player_points < dealer_points:
                    await self.set_player_loss(vk_id, player.id)

                elif player_points > dealer_points:
                    await self.set_player_win(vk_id, player.id)

                else:
                    await self.set_player_draw(vk_id, player.id)

        await self.end_game(vk_id, game_id)

    async def set_player_win(
        self, vk_id: int, player_id: int, blackjack: bool = False
    ) -> None:
        """засчитывает игроку выигрыш"""

        await self.app.store.game.add_bet_to_cash(vk_id, player_id, blackjack)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)
        await self.app.store.game.add_game_played_to_player(player_id)
        await self.app.store.game.add_game_win_to_player(player_id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_win(vk_id, vk_user.name, blackjack)

    async def set_player_draw(self, vk_id: int, player_id: int) -> None:
        """засчитывает игроку ничью"""

        await self.app.store.game.set_player_bet(player_id, None)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)
        await self.app.store.game.add_game_played_to_player(player_id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_draw(vk_id, vk_user.name)

    async def set_player_loss(self, vk_id: int, player_id: int) -> None:
        """засчитывает игроку проигрыш"""

        await self.app.store.game.withdraw_bet_from_cash(vk_id, player_id)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)
        await self.app.store.game.add_game_played_to_player(player_id)
        await self.app.store.game.add_game_loss_to_player(player_id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_loss(vk_id, vk_user.name)

    async def end_game(self, vk_id: int, game_id: int) -> None:
        """заканчивает игру"""

        await self.app.store.game.set_game_state(game_id, "inactive")
        await self.notifier.game_ended(vk_id)

        # TODO статистика

        await self.notifier.game_offer(vk_id, again=True)

    async def abort_game(
        self, vk_id: int, game_id: int, causer: str | None = None
    ) -> None:
        """метод отменяет игру (при поиске игроков или ожидании ставок)"""

        game = await self.app.store.game.get_game_by_id(game_id)
        players = await self.app.store.game.get_active_players(game_id)

        # TODO стоп таска waiting

        for player in players:
            if player.bet:
                await self.app.store.game.set_player_bet(player.id, None)
            if player.hand.get("cards"):
                await self.app.store.game.clear_player_hand(player.id)
            await self.app.store.game.set_player_state(player.id, False)

        await self.app.store.game.set_game_state(game.id, "inactive")
        await self.notifier.game_aborted(vk_id, causer)

    async def stop_game(
        self, vk_id: int, game_id: int, causer: str | None = None
    ) -> None:
        """удивительно, но этот метод останавливает игру"""

        game = await self.app.store.game.get_game_by_id(game_id)
        players = await self.app.store.game.get_active_players(game_id)

        await self.app.store.game.set_current_player(None, game.id)

        for player in players:
            await self.app.store.game.set_player_bet(player.id, None)
            if player.hand.get("cards"):
                await self.app.store.game.clear_player_hand(player.id)
            await self.app.store.game.set_player_state(player.id, False)

        await self.app.store.game.set_game_state(game.id, "inactive")
        await self.notifier.game_canceled(vk_id, causer)

    async def send_statistic(self, vk_chat_id: int, vk_user_id: int) -> None:
        """отправляет в чат статистику"""

        chat = await self.app.store.game.get_chat_by_vk_id(vk_chat_id)
        await self.notifier.chat_stat(
            vk_chat_id, chat.games_played, chat.casino_cash
        )

        game = await self.app.store.game.get_game_by_chat_id(chat.id)
        player = await self.app.store.game.get_player_by_vk_and_game(
            vk_user_id, game.id
        )
        if not player:
            vk_user = await self.app.store.vk_api.get_user(vk_user_id)
            await self.notifier.player_stat(
                vk_chat_id, vk_user.name, vk_user.sex
            )

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_stat(
            vk_chat_id,
            vk_user.name,
            vk_user.sex,
            player.games_played,
            player.games_won,
            player.games_lost,
            player.cash,
        )

    async def recover(self) -> None:
        """восстанавливает игровую сессию после отключения"""
        # TODODODODO
        raise NotImplementedError
