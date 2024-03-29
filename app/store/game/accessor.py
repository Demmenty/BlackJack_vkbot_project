from sqlalchemy import func, select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import (
    ChatModel,
    GameModel,
    GlobalSettingsModel,
    PlayerModel,
    VKUserModel,
)
from app.game.states import GameState
from app.store.game.decorators import catch_db_error


class GameAccessor(BaseAccessor):
    """взаимосвязь gamemanager и database"""

    # vk_user
    @catch_db_error
    async def create_vk_user(self, vk_id: int) -> VKUserModel:
        """создает и возвращает модель пользователя вк"""

        async with self.app.database.session() as session:
            async with session.begin():
                vk_user = await self.app.store.vk_api.get_user(vk_id)
                vk_user_model = VKUserModel(
                    vk_id=vk_id,
                    name=vk_user.name,
                    sex=vk_user.sex,
                )
                session.add(vk_user_model)
                await session.commit()

        return vk_user_model

    @catch_db_error
    async def get_vk_user_by_vk_id(self, vk_id: int) -> VKUserModel | None:
        """возвращает модель пользователя вк по его id в вк"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(VKUserModel).filter_by(vk_id=vk_id)
                result = await session.execute(q)
                vk_user = result.scalars().first()

        return vk_user

    @catch_db_error
    async def get_vk_user_by_player(self, player_id: int) -> VKUserModel | None:
        """возвращает модель пользователя вк"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(VKUserModel).filter(
                    VKUserModel.players.any(id=player_id)
                )
                result = await session.execute(q)
                vk_user = result.scalars().first()

        return vk_user

    # player
    @catch_db_error
    async def create_player(self, vk_id: int, game_id: int) -> PlayerModel:
        """создает и возвращает модель игрока"""

        global_settings = await self.get_global_settings()

        async with self.app.database.session() as session:
            async with session.begin():
                player = PlayerModel(
                    user_id=vk_id,
                    game_id=game_id,
                    cash=global_settings.start_cash,
                )
                session.add(player)
                await session.commit()

        return player

    @catch_db_error
    async def get_player_by_id(self, player_id: int) -> PlayerModel | None:
        """возвращает модель игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player = result.scalars().first()

        return player

    @catch_db_error
    async def get_player_by_vk_and_game(
        self, vk_id: int, game_id: int
    ) -> PlayerModel | None:
        """возвращает модель игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(PlayerModel)
                    .filter_by(game_id=game_id)
                    .filter(PlayerModel.vk_user.has(vk_id=vk_id))
                )
                result = await session.execute(q)
                player = result.scalars().first()

        return player

    @catch_db_error
    async def get_players_of_user(self, vk_id: int) -> list[PlayerModel]:
        """возвращает все модели игрока, соответствующие одному пользователю vk"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter(
                    PlayerModel.vk_user.has(vk_id=vk_id)
                )
                result = await session.execute(q)
                players = result.scalars().all()

        return players

    @catch_db_error
    async def set_player_cash(
        self, player_id: int, new_cash: int = 1000
    ) -> None:
        """меняет баланс игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(cash=new_cash)
                )
                await session.execute(q)

    @catch_db_error
    async def set_player_bet(self, player_id: int, new_bet: int | None) -> None:
        """меняет ставку игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(bet=new_bet)
                )
                await session.execute(q)

    @catch_db_error
    async def set_player_state(self, player_id: int, is_active: bool) -> None:
        """меняет статус игрока - активный/неактивный"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(is_active=is_active)
                )
                await session.execute(q)

    @catch_db_error
    async def add_cards_to_player(
        self, player_id: int, cards: list[str]
    ) -> None:
        """добавляет в руку игрока переданные карты"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                new_hand = player.hand.copy()
                for card in cards:
                    new_hand["cards"].append(card)

                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(hand=new_hand)
                )
                await session.execute(q)

    @catch_db_error
    async def clear_player_hand(self, player_id: int) -> None:
        """опустошает руку игрока. в смысле, от карт"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(hand={"cards": []})
                )
                await session.execute(q)

    @catch_db_error
    async def withdraw_bet_from_cash(self, vk_id: int, player_id: int) -> int:
        """уменьшает баланс игрока на его ставку, убирает ставку,
        возвращает сумму, оставшуюся на балансе игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                q = select(ChatModel).filter_by(vk_id=vk_id)
                result = await session.execute(q)
                chat: ChatModel = result.scalars().first()

                if player.bet:
                    chat.casino_cash += player.bet
                    player.cash = player.cash - player.bet
                    player.bet = None

                    await session.commit()

        return player.cash

    @catch_db_error
    async def add_bet_to_cash(
        self, vk_id: int, player_id: int, blackjack: bool = False
    ) -> None:
        """увеличивает баланс игрока на его ставку, убирает ставку"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                q = select(ChatModel).filter_by(vk_id=vk_id)
                result = await session.execute(q)
                chat: ChatModel = result.scalars().first()

                if blackjack:
                    player_bet = player.bet * 1.5
                else:
                    player_bet = player.bet

                chat.casino_cash -= player_bet
                player.cash = player.cash + player_bet
                player.bet = None
                await session.commit()

    @catch_db_error
    async def get_players(self, game_id: int) -> list[PlayerModel]:
        """возвращает список всех игроков"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(game_id=game_id)
                result = await session.execute(q)
                players = result.scalars().all()

        return players

    @catch_db_error
    async def get_active_players(self, game_id: int) -> list[PlayerModel]:
        """возвращает список игроков с is_active=True"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(
                    game_id=game_id, is_active=True
                )
                result = await session.execute(q)
                players = result.scalars().all()

        return players

    @catch_db_error
    async def count_losers(self, game_id: int) -> int:
        """возвращает количество игроков с cash = 0"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(func.count())
                    .select_from(PlayerModel)
                    .filter_by(cash=0, game_id=game_id)
                )
                result = await session.execute(q)
                amount = result.scalar()

        return amount

    @catch_db_error
    async def add_game_played_to_player(self, player_id: int) -> None:
        """добавляет еще одну игру в статистику игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()
                player.games_played += 1
                await session.commit()

    @catch_db_error
    async def add_game_win_to_player(self, player_id: int) -> None:
        """добавляет еще одну выигранную игру в статистику игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()
                player.games_won += 1
                await session.commit()

    @catch_db_error
    async def add_game_loss_to_player(self, player_id: int) -> None:
        """добавляет еще одну проигранную игру в статистику игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()
                player.games_lost += 1
                await session.commit()

    # chat
    @catch_db_error
    async def create_chat(self, vk_id: int) -> ChatModel:
        """создает и возвращает модель чата, vk_id = peer_id из vk"""

        async with self.app.database.session() as session:
            async with session.begin():
                chat = ChatModel(vk_id=vk_id)
                session.add(chat)
                await session.commit()

        return chat

    @catch_db_error
    async def get_chat_by_vk_id(self, vk_id: int) -> ChatModel | None:
        """возвращает модель чата, vk_id = peer_id из vk"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ChatModel).filter_by(vk_id=vk_id)

                result = await session.execute(q)
                chat = result.scalars().first()

        return chat

    @catch_db_error
    async def get_chat_by_game_id(self, game_id: int) -> ChatModel:
        """возвращает модель чата"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ChatModel).filter(ChatModel.game.any(id=game_id))
                result = await session.execute(q)
                chat = result.scalars().first()

        return chat

    @catch_db_error
    async def add_game_played_to_chat(self, vk_id: int) -> None:
        """добавляет еще одну игру в статистику чата"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ChatModel).filter_by(vk_id=vk_id)
                result = await session.execute(q)
                chat: ChatModel = result.scalars().first()
                chat.games_played += 1
                await session.commit()

    # game
    @catch_db_error
    async def create_game(self, chat_id: int) -> GameModel:
        """создает и возвращает модель игры для чата"""

        async with self.app.database.session() as session:
            async with session.begin():
                game = GameModel(chat_id=chat_id)
                session.add(game)
                await session.commit()

        return game

    @catch_db_error
    async def get_game_by_chat_id(self, chat_id: int) -> GameModel | None:
        """возвращает модель игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter_by(chat_id=chat_id)
                result = await session.execute(q)
                game = result.scalars().first()

        return game

    @catch_db_error
    async def get_game_by_id(self, game_id: int) -> GameModel:
        """возвращает модель игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter_by(id=game_id)
                result = await session.execute(q)
                game = result.scalars().first()

        return game

    @catch_db_error
    async def get_game_by_vk_id(self, vk_id: int) -> GameModel | None:
        """возвращает модель игры по peer_id из vk"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter(GameModel.chat.has(vk_id=vk_id))
                result = await session.execute(q)
                game = result.scalars().first()

        return game

    @catch_db_error
    async def is_game_on(self, vk_id: int) -> bool:
        """предикат, проверяющий, в процессе ли игра в чате по peer_id из vk"""

        game = await self.get_game_by_vk_id(vk_id=vk_id)

        return game and game.state != GameState.inactive

    @catch_db_error
    async def set_game_state(self, game_id: int, new_state: GameState) -> None:
        """меняет статус игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(state=new_state.name)
                )
                await session.execute(q)

    @catch_db_error
    async def get_active_games(self) -> list[GameModel]:
        """возвращает список активных игр"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter(
                    GameModel.state != GameState.inactive
                )
                result = await session.execute(q)
                games = result.scalars().all()

        return games

    @catch_db_error
    async def set_current_player(
        self, game_id: int, player_id: int | None
    ) -> None:
        """отмечает в базе, что сейчас ход переданного игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(current_player_id=player_id)
                )
                await session.execute(q)

    @catch_db_error
    async def set_dealer_hand_and_points(
        self, game_id: int, cards: list[str], points: int | None
    ) -> None:
        """записывает набранные дилером карты и очки"""

        new_hand = {"cards": cards}

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(dealer_points=points, dealer_hand=new_hand)
                )
                await session.execute(q)

    @catch_db_error
    async def clear_dealer_hand_and_points(self, game_id: int) -> None:
        """опустошает руку дилера от карт и удаляет очки"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(dealer_hand={"cards": []}, dealer_points=None)
                )
                await session.execute(q)

    # global_settings
    @catch_db_error
    async def create_global_settings(self) -> None:
        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GlobalSettingsModel)
                result = await session.execute(q)
                global_settings = result.scalars().first()

                if not global_settings:
                    global_settings = GlobalSettingsModel()
                    session.add(global_settings)
                    await session.commit()

    @catch_db_error
    async def get_global_settings(self) -> GlobalSettingsModel | None:
        """возвращает модель глобальных настроек"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GlobalSettingsModel).filter_by(id=1)
                result = await session.execute(q)
                global_settings = result.scalars().first()

        return global_settings

    @catch_db_error
    async def set_start_cash(self, start_cash: int) -> None:
        """записывает число стартовых монет в бд"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GlobalSettingsModel)
                    .filter_by(id=1)
                    .values(start_cash=start_cash)
                )
                await session.execute(q)

    # комплексные транзакции
    @catch_db_error
    async def set_player_win(
        self, player_id: int, blackjack: bool = False
    ) -> None:
        """регистрирует победу игрока:
        увеличивает баланс на ставку,
        вносит инфо в статистику,
        инактивирует игрока и очищает нужные поля"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                q = select(ChatModel).filter(
                    ChatModel.game.any(id=player.game_id)
                )
                result = await session.execute(q)
                chat: ChatModel = result.scalars().first()

                if blackjack:
                    player_bet = player.bet * 1.5
                else:
                    player_bet = player.bet

                chat.casino_cash -= player_bet

                player.cash += player_bet
                player.bet = None
                player.hand = {"cards": []}
                player.is_active = False
                player.games_played += 1
                player.games_won += 1

                await session.commit()

    @catch_db_error
    async def set_player_loss(self, player_id: int) -> None:
        """регистрирует проигрыш игрока:
        уменьшает баланс на ставку,
        вносит инфо в статистику,
        инактивирует игрока и очищает нужные поля"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                q = select(ChatModel).filter(
                    ChatModel.game.any(id=player.game_id)
                )
                result = await session.execute(q)
                chat: ChatModel = result.scalars().first()

                chat.casino_cash += player.bet

                player.cash -= player.bet
                player.bet = None
                player.hand = {"cards": []}
                player.is_active = False
                player.games_played += 1
                player.games_lost += 1

                await session.commit()

    @catch_db_error
    async def set_player_draw(self, player_id: int) -> None:
        """регистрирует ничью:
        вносит инфо в статистику,
        инактивирует игрока и очищает нужные поля"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                player.bet = None
                player.hand = {"cards": []}
                player.is_active = False
                player.games_played += 1

                await session.commit()
