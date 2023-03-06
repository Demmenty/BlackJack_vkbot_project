from sqlalchemy import select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import ChatModel, GameModel, PlayerModel, VKUserModel


class GameAccessor(BaseAccessor):
    """взаимосвязь gamemanager и database"""

    async def get_or_create_vk_user(self, vk_user_id: int) -> VKUserModel:
        """возвращает VKUserModel, если нет - создает и возвращает.
        передать vk_user_id (это user_id из vk update)"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(VKUserModel).filter_by(vk_user_id=vk_user_id)
                result = await session.execute(q)
                vk_user = result.scalars().first()

                if not vk_user:
                    name = await self.app.store.vk_api.get_username(
                        vk_user_id=vk_user_id
                    )
                    vk_user = VKUserModel(vk_user_id=vk_user_id, name=name)
                    session.add(vk_user)
                    await session.commit()

        return vk_user

    async def get_or_create_player(
        self, vk_user_id: int, game_id: int
    ) -> tuple[PlayerModel, bool]:
        """регистрирует пользователя в качестве игрока,
        возвращает кортеж: его модель и предикат is_created"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(
                    user_id=vk_user_id, game_id=game_id
                )
                result = await session.execute(q)
                player = result.scalars().first()
                is_created = False

                if not player:
                    player = PlayerModel(user_id=vk_user_id, game_id=game_id)
                    session.add(player)
                    await session.commit()
                    is_created = True

        return player, is_created

    async def get_player_by_id(self, player_id: int) -> PlayerModel | None:
        """возвращает модель игрока из базы данных"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player = result.scalars().first()

        return player

    async def get_player_by_vk_and_game(
        self, vk_user_id: int, game_id: int
    ) -> PlayerModel | None:
        """возвращает модель игрока из базы данных"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(PlayerModel)
                    .filter_by(game_id=game_id)
                    .filter(PlayerModel.vk_user.has(vk_user_id=vk_user_id))
                )
                result = await session.execute(q)
                player = result.scalars().first()

        return player

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

    async def get_player_name(self, player_id: int) -> str:
        """возвращает имя игрока из базы по его id"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(VKUserModel.name)
                    .join_from(VKUserModel, PlayerModel)
                    .filter_by(id=player_id)
                )
                result = await session.execute(q)
                name = result.scalars().first()

        return name

    async def get_player_vk_id(self, player_id: int) -> int:
        """возвращает vk user_id игрока"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(VKUserModel.vk_user_id)
                    .join_from(VKUserModel, PlayerModel)
                    .filter_by(id=player_id)
                )
                result = await session.execute(q)
                vk_id = result.scalars().first()

        return vk_id

    async def set_player_state(self, player_id: int, is_active: bool) -> None:
        """меняет статус игрока - активный/неактивный, передать желаемое значение в bool"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(PlayerModel)
                    .filter_by(id=player_id)
                    .values(is_active=is_active)
                )
                await session.execute(q)

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

    async def withdraw_bet_from_cash(self, player_id: int) -> None:
        """уменьшает баланс игрока на его ставку, убирает ставку"""
        # TODO change_casino_cash

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                player.cash = player.cash - player.bet
                player.bet = None
                await session.commit()

    async def add_bet_to_cash(
        self, player_id: int, blackjack: bool = False
    ) -> None:
        """увеличивает баланс игрока на его ставку, убирает ставку"""
        # TODO change_casino_cash

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(PlayerModel).filter_by(id=player_id)
                result = await session.execute(q)
                player: PlayerModel = result.scalars().first()

                if blackjack:
                    player.cash = player.cash + player.bet * 1.5
                else:
                    player.cash = player.cash + player.bet

                player.bet = None
                await session.commit()

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

    async def get_or_create_chat(self, vk_peer_id: int) -> ChatModel:
        """возвращает ChatModel, если нет - создает и возвращает.
        передать vk_peer_id (это peer_id из vk updte)"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ChatModel).filter_by(vk_peer_id=vk_peer_id)
                result = await session.execute(q)
                chat = result.scalars().first()

                if not chat:
                    chat = ChatModel(vk_peer_id=vk_peer_id)
                    session.add(chat)
                    await session.commit()

        return chat

    async def get_or_create_game(self, peer_id: int) -> GameModel:
        """возвращает GameModel, если нет - создает неактивную
        передать chat_id (это peer_id из vk)"""

        chat = await self.get_or_create_chat(vk_peer_id=peer_id)

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter_by(chat_id=chat.id)
                result = await session.execute(q)
                game = result.scalars().first()

                if not game:
                    game = GameModel(chat_id=chat.id, state="inactive")
                    session.add(game)
                    await session.commit()

        return game

    async def get_game_by_id(self, game_id: int) -> GameModel:
        """возвращает модель игры по ее id"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter_by(id=game_id)
                result = await session.execute(q)
                game = result.scalars().first()

        return game

    async def get_game_by_peer_id(self, peer_id: int) -> GameModel | None:
        """возвращает GameModel по peer_id из vk"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter(
                    GameModel.chat.has(vk_peer_id=peer_id)
                )
                result = await session.execute(q)
                game = result.scalars().first()

        return game

    async def is_game_on(self, peer_id: int) -> bool:
        """предикат, проверяющий, в процессе ли игра в чате по peer_id из vk"""

        game = await self.get_game_by_peer_id(peer_id=peer_id)

        # TODO cтейты вынести в енам! -> (game.state != State.INACTIVE)
        result = game and game.state != "inactive"

        return result

    async def set_game_state(self, game_id: int, new_state: str) -> None:
        """меняет статус игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(state=new_state)
                )
                await session.execute(q)

    async def set_current_player(
        self, player_id: int | None, game_id: int
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

    async def set_dealer_points(self, game_id: int, points: int) -> None:
        """записывает набранные дилером очки"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    update(GameModel)
                    .filter_by(id=game_id)
                    .values(dealer_points=points)
                )
                await session.execute(q)

    async def get_dealer_points(self, game_id: int) -> int:
        """возвращает набранные дилером очки"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel.dealer_points).filter_by(id=game_id)
                result = await session.execute(q)
                dealer_points = result.scalars().first()

        return dealer_points
