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

    async def start_game(self, peer_id: int) -> None:
        """начинает новую игру"""

        await self.notifier.game_starting(peer_id)

        game = await self.app.store.game.get_or_create_game(peer_id)

        await self.define_players(peer_id, game.id)

    async def define_players(
        self,
        peer_id: int,
        game_id: int,
    ) -> None:
        """собирает игроков"""

        await self.app.store.game.set_game_state(game_id, "define_players")

        await self.notifier.waiting_players(peer_id)

        create_task(self.waiting_players(peer_id, game_id))
        # TODO организовать какой-то там коллбек

    async def waiting_players(self, peer_id: int, game_id: int) -> None:
        """ждет, пока отметятся игроки"""

        await asleep(15)

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.notifier.no_players(peer_id)
            await self.abort_game(peer_id, game_id)
            return

        players_names: list[str] = [
            await self.app.store.game.get_player_name(player.id)
            for player in players
        ]
        await self.notifier.active_players(peer_id, players_names)
        await self.start_betting(peer_id, game_id)

    async def start_betting(self, peer_id: int, game_id: int) -> None:
        """начинает стадию ставок"""

        await self.app.store.game.set_game_state(game_id, "betting")
        await self.notifier.waiting_bets(peer_id)

        create_task(self.waiting_bets(peer_id, game_id))
        # TODO организовать какой-то там коллбек

    async def waiting_bets(self, peer_id: int, game_id: int) -> None:
        """ждет, пока игроки не сделают ставки,
        тогда направляет на стадию раздачи карт"""

        await asleep(20)

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.notifier.no_players(peer_id)
            await self.abort_game(peer_id, game_id)
            return

        bets_are_made = True
        for player in players:
            if player.bet is None:
                bets_are_made = False
                name = await self.app.store.game.get_player_name(player.id)
                await self.notifier.no_bet(peer_id, name)

        # бот будет ждать ставки бесконечно, но на данном этопе любой игрок может отменить игру
        if not bets_are_made:
            create_task(self.waiting_bets(peer_id, game_id))
            return

        await self.start_dealing(peer_id, game_id)

    async def start_dealing(self, peer_id: int, game_id: int) -> None:
        """начинает стадию раздачи карт"""

        await self.app.store.game.set_game_state(game_id, "dealing")
        await self.notifier.dealing_started(peer_id)

        players = await self.app.store.game.get_active_players(game_id)

        # TODO возможно, убрать показ игроков тут, подумать
        players_names: list[str] = [
            await self.app.store.game.get_player_name(player.id)
            for player in players
        ]
        await self.notifier.active_players(peer_id, players_names)

        # TODO транзакции
        player = random.choice(players)

        await self.app.store.game.set_current_player(player.id, game_id)

        name = await self.app.store.game.get_player_name(player.id)
        await self.notifier.player_turn(peer_id, name)

        await self.deal_cards_to_player(2, peer_id, game_id, player.id)
        # TODO поставить таймер - отсутствие команды считать как "хватит"

    async def deal_cards_to_player(
        self, amount: int, peer_id: int, game_id: int, player_id: int
    ) -> None:
        """выдает игроку карты в указанном количестве"""

        # TODO попробовать в круглых скобках
        cards = [self.deck.take_a_card() for card in range(amount)]

        await self.app.store.game.add_cards_to_player(player_id, cards)
        await self.notifier.cards_received(peer_id, cards)

        await self.check_player_hand(peer_id, game_id, player_id)

    async def check_player_hand(
        self, peer_id: int, game_id: int, player_id: int
    ) -> None:
        """проверяет сумму карт в руке игрока и делает выводы"""

        player = await self.app.store.game.get_player_by_id(player_id)
        player_cards = player.hand["cards"]
        player_points = self.deck.count_points(player_cards)

        if player_points == 21:
            if len(player_cards) == 2:
                name = await self.app.store.game.get_player_name(player_id)
                await self.notifier.player_blackjack(player_id, name)
            await self.set_next_player_turn(peer_id, game_id)
            return

        if player_points > 21:
            await self.notifier.player_overflow(peer_id)
            await self.set_player_loss(peer_id, player_id)
            await self.set_next_player_turn(peer_id, game_id)
            return

        if player_points < 21:
            await self.notifier.offer_a_card(peer_id)
            # TODO вот тут мб запустить таймер: нет ответа = хватит

        # PS я сравниваю числа в этом месте лишний раз тупо для красоты и наглядности

    async def set_next_player_turn(self, peer_id: int, game_id: int) -> None:
        """раздает карты следующему игроку"""

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.end_game(peer_id, game_id)
            return

        players_without_cards = [
            player for player in players if not player.hand["cards"]
        ]

        if not players_without_cards:
            await self.deal_to_dealer(peer_id, game_id)
            return

        player = random.choice(players_without_cards)

        await self.app.store.game.set_current_player(player.id, game_id)

        name = await self.app.store.game.get_player_name(player.id)
        await self.notifier.player_turn(peer_id, name)

        await self.deal_cards_to_player(2, peer_id, game_id, player.id)
        # TODO поставить таймер - отсутствие команды считать как "хватит"

    async def deal_to_dealer(self, peer_id: int, game_id: int) -> None:
        """раздает карты дилеру"""

        await self.notifier.deal_to_dealer(peer_id)

        dealer_cards = [self.deck.take_a_card(), self.deck.take_a_card()]
        dealer_points = self.deck.count_points(dealer_cards)

        while dealer_points < 17:
            dealer_cards.append(self.deck.take_a_card())
            dealer_points = self.deck.count_points(dealer_cards)

        await self.app.store.game.set_dealer_points(game_id, dealer_points)
        await self.notifier.cards_received(peer_id, dealer_cards)

        await self.sum_up_results(peer_id, game_id)

    async def sum_up_results(self, peer_id: int, game_id: int) -> None:
        """сравнивает очки оставшихся игроков и дилера, подводя итоги"""

        players = await self.app.store.game.get_active_players(game_id)
        dealer_points = await self.app.store.game.get_dealer_points(game_id)

        if dealer_points > 21:
            for player in players:
                if self.deck.is_blackjack(player.hand["cards"]):
                    await self.set_player_win(
                        peer_id, player.id, blackjack=True
                    )
                else:
                    await self.set_player_win(peer_id, player.id)
        else:
            for player in players:
                player_points = self.deck.count_points(player.hand["cards"])

                if (
                    self.deck.is_blackjack(player.hand["cards"])
                    and dealer_points < 21
                ):
                    await self.set_player_win(
                        peer_id, player.id, blackjack=True
                    )
                elif player_points < dealer_points:
                    await self.set_player_loss(peer_id, player.id)

                elif player_points > dealer_points:
                    await self.set_player_win(peer_id, player.id)

                else:
                    await self.set_player_draw(peer_id, player.id)

        await self.end_game(peer_id, game_id)

    async def set_player_win(
        self, peer_id: int, player_id: int, blackjack: bool = False
    ) -> None:
        """засчитывает игроку выигрыш"""

        await self.app.store.game.add_bet_to_cash(player_id, blackjack)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)

        name = await self.app.store.game.get_player_name(player_id)
        await self.notifier.player_win(peer_id, name)

    async def set_player_draw(self, peer_id: int, player_id: int) -> None:
        """засчитывает игроку ничью"""

        await self.app.store.game.set_player_bet(player_id, None)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)

        name = await self.app.store.game.get_player_name(player_id)
        await self.notifier.player_draw(peer_id, name)

    async def set_player_loss(self, peer_id: int, player_id: int) -> None:
        """засчитывает игроку проигрыш"""

        await self.app.store.game.withdraw_bet_from_cash(player_id)
        await self.app.store.game.clear_player_hand(player_id)
        await self.app.store.game.set_player_state(player_id, False)

        name = await self.app.store.game.get_player_name(player_id)
        await self.notifier.player_loss(peer_id, name)

    async def end_game(self, peer_id: int, game_id: int) -> None:
        """заканчивает игру, выводит статистику"""

        await self.app.store.game.set_game_state(game_id, "inactive")
        await self.notifier.game_ended(peer_id)

        await self.notifier.game_offer(peer_id, again=True)
        # TODO статистика

    async def abort_game(
        self, peer_id: int, game_id: int, causer: str | None = None
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
        await self.notifier.game_aborted(peer_id, causer)

    async def stop_game(
        self, peer_id: int, game_id: int, causer: str | None = None
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
        await self.notifier.game_canceled(peer_id, causer)

        # TODO собрать и показать какие-то результаты

    async def recover(self) -> None:
        """восстанавливает игровую сессию после отключения"""
        # TODODODODO
        raise NotImplementedError
