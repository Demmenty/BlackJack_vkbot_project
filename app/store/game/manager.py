import random
import typing
from asyncio import create_task
from logging import getLogger

from app.game.models import GameModel
from app.game.states import GameState
from app.store.game.decks import EndlessDeck
from app.store.game.notifications import GameNotifier
from app.store.game.timer import GameTimerManager

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameManager:
    """управление процессом игры"""

    def __init__(self, app: "Application"):
        self.app = app
        app.on_startup.append(self.connect)
        app.on_shutdown.append(self.disconnect)
        self.notifier = GameNotifier(app)
        self.deck = EndlessDeck()
        self.timer = GameTimerManager()
        self.logger = getLogger("game manager")

    async def start_game(self, vk_id: int, game_id: int) -> None:
        """запускает новую игру, направляет на стадию сбора игроков"""

        self.logger.info(f"start_game, vk_id={vk_id}, game_id={game_id}")

        await self.notifier.game_starting(vk_id)

        await self.gathering_players(vk_id, game_id)

    async def gathering_players(self, vk_id: int, game_id: int) -> None:
        """запускает стадию набора игроков"""

        self.logger.info(f"gathering_players, vk_id={vk_id}, game_id={game_id}")

        await self.app.store.game.set_game_state(game_id, GameState.gathering)
        await self.notifier.waiting_players(vk_id)

        create_task(
            self.timer.start_timer(
                sec=30,
                vk_id=vk_id,
                game_id=game_id,
                next_method=self.collect_players,
            )
        )

    async def collect_players(self, vk_id: int, game_id: int) -> None:
        """проверяет наличие игроков и направляет на стадию ставок, если есть"""

        self.logger.info(f"collect_players, vk_id={vk_id}, game_id={game_id}")

        players = await self.app.store.game.get_active_players(game_id)

        if not players:
            await self.notifier.no_players(vk_id)
            await self.inactivate_game(game_id)
            await self.notifier.game_aborted(vk_id)
            return

        players_names: list[str] = []
        for player in players:
            vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
            players_names.append(vk_user.name)

        await self.notifier.active_players(vk_id, players_names)
        await self.start_betting(vk_id, game_id)

    async def start_betting(self, vk_id: int, game_id: int) -> None:
        """запускает ожидание ставок"""

        self.logger.info(f"start_betting, vk_id={vk_id}, game_id={game_id}")

        await self.app.store.game.set_game_state(game_id, GameState.betting)
        await self.notifier.waiting_bets(vk_id)

        create_task(
            self.timer.start_timer(
                sec=60,
                vk_id=vk_id,
                game_id=game_id,
                next_method=self.collect_bets,
            )
        )

    async def collect_bets(self, vk_id: int, game_id: int) -> None:
        """проверяет наличие ставок игроков, инактивирует непоставивших,
        и направляет на стадию раздачи, если есть поставившие"""

        self.logger.info(f"collect_bets, vk_id={vk_id}, game_id={game_id}")

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
            await self.inactivate_game(game_id)
            await self.notifier.game_aborted(vk_id)
            return

        await self.start_dealing(vk_id, game_id)

    async def start_dealing(self, vk_id: int, game_id: int) -> None:
        """запускает стадию раздачи карт"""

        self.logger.info(f"start_dealing, vk_id={vk_id}, game_id={game_id}")

        # сыгранной игрой будет считаться игра, дошедшая до раздачи
        await self.app.store.game.add_game_played_to_chat(vk_id)
        await self.app.store.game.set_game_state(
            game_id, GameState.dealing_players
        )
        await self.notifier.dealing_started(vk_id)

        players = await self.app.store.game.get_active_players(game_id)

        # TODO транзакции
        player = random.choice(players)

        await self.app.store.game.set_current_player(game_id, player.id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_turn(vk_id, vk_user.name, vk_user.sex)

        await self.deal_cards_to_player(2, vk_id, game_id, player.id)

    async def deal_cards_to_player(
        self, amount: int, vk_id: int, game_id: int, player_id: int
    ) -> None:
        """выдает игроку карты в указанном количестве"""

        self.logger.info(
            f"deal_cards_to_player, vk_id={vk_id}, game_id={game_id}, player_id={player_id}"
        )

        cards = [self.deck.take_a_card() for card in range(amount)]

        await self.app.store.game.add_cards_to_player(player_id, cards)
        await self.notifier.cards_received(vk_id, cards)

        await self.check_player_hand(vk_id, game_id, player_id)

    async def check_player_hand(
        self, vk_id: int, game_id: int, player_id: int
    ) -> None:
        """проверяет сумму карт в руке игрока и делает выводы"""

        self.logger.info(
            f"_check_player_hand, vk_id={vk_id}, game_id={game_id}, player_id={player_id}"
        )

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

            create_task(
                self.timer.start_timer(
                    sec=60,
                    vk_id=vk_id,
                    game_id=game_id,
                    next_method=self.set_next_player_turn,
                )
            )

    async def set_next_player_turn(self, vk_id: int, game_id: int) -> None:
        """запускает раздачу карт следующему игроку"""

        self.logger.info(
            f"_check_player_hand, vk_id={vk_id}, game_id={game_id}"
        )

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

        await self.app.store.game.set_current_player(game_id, player.id)

        vk_user = await self.app.store.game.get_vk_user_by_player(player.id)
        await self.notifier.player_turn(vk_id, vk_user.name, vk_user.sex)

        await self.deal_cards_to_player(2, vk_id, game_id, player.id)

    async def deal_to_dealer(self, vk_id: int, game_id: int) -> None:
        """запускает раздачу карт дилеру"""

        self.logger.info(f"deal_to_dealer, vk_id={vk_id}, game_id={game_id}")

        await self.app.store.game.set_game_state(
            game_id, GameState.dealing_dealer
        )
        await self.notifier.deal_to_dealer(vk_id)

        dealer_cards = [self.deck.take_a_card(), self.deck.take_a_card()]
        dealer_points = self.deck.count_points(dealer_cards)

        while dealer_points < 17:
            dealer_cards.append(self.deck.take_a_card())
            dealer_points = self.deck.count_points(dealer_cards)

        await self.app.store.game.set_dealer_hand_and_points(
            game_id, dealer_cards, dealer_points
        )

        await self.notifier.cards_received(vk_id, dealer_cards)

        await self.sum_up_results(vk_id, game_id)

    async def sum_up_results(self, vk_id: int, game_id: int) -> None:
        """сравнивает очки оставшихся игроков и дилера, подводя итоги"""

        self.logger.info(f"sum_up_results, vk_id={vk_id}, game_id={game_id}")

        await self.app.store.game.set_game_state(game_id, GameState.results)

        players = await self.app.store.game.get_active_players(game_id)
        game = await self.app.store.game.get_game_by_id(game_id)

        if not game.dealer_points:
            await self.inactivate_game(game_id)
            return

        if game.dealer_points > 21:
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
                    and game.dealer_points < 21
                ):
                    await self.set_player_win(vk_id, player.id, blackjack=True)
                elif player_points < game.dealer_points:
                    await self.set_player_loss(vk_id, player.id)

                elif player_points > game.dealer_points:
                    await self.set_player_win(vk_id, player.id)

                else:
                    await self.set_player_draw(vk_id, player.id)

        await self.end_game(vk_id, game_id)

    async def set_player_win(
        self, vk_id: int, player_id: int, blackjack: bool = False
    ) -> None:
        """засчитывает игроку выигрыш"""

        self.logger.info(
            f"set_player_win, vk_id={vk_id}, player_id={player_id}, blackjack={blackjack}"
        )

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_win(vk_id, vk_user.name, blackjack)

        await self.app.store.game.set_player_win(player_id, blackjack)

    async def set_player_draw(self, vk_id: int, player_id: int) -> None:
        """засчитывает игроку ничью"""

        self.logger.info(
            f"set_player_draw, vk_id={vk_id}, player_id={player_id}"
        )

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_draw(vk_id, vk_user.name)

        await self.app.store.game.set_player_draw(player_id)

    async def set_player_loss(self, vk_id: int, player_id: int) -> None:
        """засчитывает игроку проигрыш"""

        self.logger.info(
            f"set_player_loss, vk_id={vk_id}, player_id={player_id}"
        )

        vk_user = await self.app.store.game.get_vk_user_by_player(player_id)
        await self.notifier.player_loss(vk_id, vk_user.name)

        await self.app.store.game.set_player_loss(player_id)

        player = await self.app.store.game.get_player_by_id(player_id)
        if not player.cash:
            await self.notifier.last_cash_spent(
                vk_id, vk_user.name, vk_user.sex
            )

    async def end_game(self, vk_id: int, game_id: int) -> None:
        """заканчивает игру"""

        self.logger.info(f"end_game, vk_id={vk_id}, game_id={game_id}")

        await self.app.store.game.set_game_state(game_id, GameState.inactive)
        await self.app.store.game.set_current_player(game_id, None)
        await self.app.store.game.clear_dealer_hand_and_points(game_id)

        await self.notifier.game_ended(vk_id)
        await self.notifier.game_offer(vk_id, again=True)

    async def send_statistic(self, vk_chat_id: int, vk_user_id: int) -> None:
        """отправляет в чат статистику"""

        self.logger.info(
            f"send_statistic, vk_chat_id={vk_chat_id}, vk_user_id={vk_user_id}"
        )

        chat = await self.app.store.game.get_chat_by_vk_id(vk_chat_id)
        if not chat:
            await self.notifier.chat_stat(vk_chat_id, 0, 0)
            return

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
            return

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

    async def connect(self, app: "Application") -> None:
        """проверка при запуске на наличие активных игр. если такие есть,
        уведомляет чат о возвращении и отправляет игру в восстановительную функцию
        """

        active_games = await self.app.store.game.get_active_games()

        for game in active_games:
            chat = await self.app.store.game.get_chat_by_game_id(game.id)
            await self.notifier.bot_returning(chat.vk_id)

            await self.recovery(chat.vk_id, game)

    # TODO возможно будет лучше выглядеть с match-case

    async def recovery(self, vk_chat_id: int, game: GameModel) -> None:
        """восстанавливает активную игру после отключения сервера"""

        if game.state == GameState.gathering:
            self.logger.info(
                f"recovery_game, vk_chat_id={vk_chat_id}, game={game}"
            )
            await self.gathering_players(vk_chat_id, game.id)
            return

        if game.state == GameState.betting:
            self.logger.info(
                f"recovery_game, vk_chat_id={vk_chat_id}, game={game}"
            )
            active_players = await self.app.store.game.get_active_players(
                game.id
            )

            if all(player.bet for player in active_players):
                await self.notifier.all_bets_placed(vk_chat_id)
                await self.app.store.game_manager.start_dealing(
                    vk_chat_id, game.id
                )
            else:
                await self.start_betting(vk_chat_id, game.id)

            return

        if game.state == GameState.dealing_players:
            self.logger.info(
                f"recovery_game, vk_chat_id={vk_chat_id}, game={game}"
            )
            if not game.current_player_id:
                await self.start_dealing(vk_chat_id, game.id)
                return

            current_player = await self.app.store.game.get_player_by_id(
                game.current_player_id
            )
            vk_user = await self.app.store.game.get_vk_user_by_player(
                current_player.id
            )

            if current_player.hand["cards"]:
                await self.notifier.player_hand(
                    vk_chat_id, vk_user.name, current_player.hand["cards"]
                )
                await self.check_player_hand(
                    vk_chat_id, game.id, current_player.id
                )
            else:
                await self.notifier.player_turn(
                    vk_chat_id, vk_user.name, vk_user.sex
                )
                await self.deal_cards_to_player(
                    2, vk_chat_id, game.id, current_player.id
                )

            return

        if game.state == GameState.dealing_dealer:
            self.logger.info(
                f"recovery_game, vk_chat_id={vk_chat_id}, game={game}"
            )

            if not game.dealer_hand["cards"]:
                await self.deal_to_dealer(vk_chat_id, game.id)
                return

            await self.notifier.cards_received(
                vk_chat_id, game.dealer_hand["cards"]
            )
            await self.sum_up_results(vk_chat_id, game.id)

        if game.state == GameState.results:
            self.logger.info(
                f"recovery_game, vk_chat_id={vk_chat_id}, game={game}"
            )
            await self.sum_up_results(vk_chat_id, game.id)
            return

    async def inactivate_game(self, game_id: int) -> None:
        """делает игру неактивной и очищает соответствующие поля в базе"""

        self.logger.info(f"inactivate_game, game_id={game_id}")

        await self.timer.end_timer(game_id)

        game = await self.app.store.game.get_game_by_id(game_id)

        if game.current_player_id:
            await self.app.store.game.set_current_player(game.id, None)
        if game.dealer_hand["cards"]:
            await self.app.store.game.clear_dealer_hand_and_points(game.id)

        active_players = await self.app.store.game.get_active_players(game.id)

        for player in active_players:
            if player.bet:
                await self.app.store.game.set_player_bet(player.id, None)
            if player.hand["cards"]:
                await self.app.store.game.clear_player_hand(player.id)
            await self.app.store.game.set_player_state(player.id, False)

        await self.app.store.game.set_game_state(game.id, GameState.inactive)

    async def disconnect(self, app: "Application") -> None:
        """проверка при отключении на наличие активных игр.
        если такие есть, уведомляет ее чат о своем отключении
        """

        active_games = await self.app.store.game.get_active_games()

        for game in active_games:
            chat = await self.app.store.game.get_chat_by_game_id(game.id)
            await self.notifier.bot_leaving(chat.vk_id)
