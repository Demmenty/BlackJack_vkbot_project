import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.game.models import ChatModel, GameModel, PlayerModel, VKUserModel


@pytest.fixture
async def vk_user_1(db_session: AsyncSession) -> VKUserModel:
    """модель пользователя, не являющегося игроком"""

    async with db_session.begin() as session:
        vk_user = VKUserModel(vk_id=93683216, name="Demmenty", sex="male")
        session.add(vk_user)

    return vk_user


@pytest.fixture
async def vk_user_2(db_session: AsyncSession) -> VKUserModel:
    """модель пользователя, являющегося игроком в двух играх"""

    async with db_session.begin() as session:
        vk_user = VKUserModel(vk_id=92693220, name="Юлия", sex="female")
        session.add(vk_user)

        chat_1 = ChatModel(vk_id=2000000001)
        session.add(chat_1)

        chat_2 = ChatModel(vk_id=2000000002)
        session.add(chat_2)

        game_1 = GameModel(chat_id=1)
        session.add(game_1)

        game_2 = GameModel(chat_id=2)
        session.add(game_2)

        player_1 = PlayerModel(
            user_id=1,
            game_id=1,
            games_played=2,
            games_won=1,
            games_lost=0,
        )
        session.add(player_1)

        player_2 = PlayerModel(
            user_id=1,
            game_id=2,
            games_played=5,
            games_won=3,
            games_lost=2,
        )
        session.add(player_2)

    return vk_user


@pytest.fixture
async def vk_user_3(db_session: AsyncSession) -> VKUserModel:
    """модель пользователя, являющегося игроком в одной игре"""

    async with db_session.begin() as session:
        vk_user = VKUserModel(vk_id=92693220, name="Юлия", sex="female")
        session.add(vk_user)

        chat_1 = ChatModel(vk_id=2000000001)
        session.add(chat_1)

        game_1 = GameModel(chat_id=1)
        session.add(game_1)

        player_1 = PlayerModel(
            user_id=1,
            game_id=1,
            games_played=2,
            games_won=1,
            games_lost=0,
        )
        session.add(player_1)

    return vk_user
