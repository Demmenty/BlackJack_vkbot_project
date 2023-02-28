from sqlalchemy import select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import ChatModel, GameModel


class GameAccessor(BaseAccessor):
    """взаимосвязь gamemanager и database"""

    async def create_game(self, peer_id: int) -> GameModel:
        """создание записи о новой неактивной игре и связи с чатом"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(ChatModel).filter_by(vk_peer_id=peer_id)
                result = await session.execute(q)
                chat = result.scalars().first()

                if not chat:
                    chat = await self.create_chat(peer_id)

                game = GameModel(
                    peer_id=chat.id,
                )
                session.add(game)
                await session.commit()

        return game

    async def create_chat(self, peer_id: int) -> ChatModel:
        """создание новой записи о чате"""

        async with self.app.database.session() as session:
            async with session.begin():
                chat = ChatModel(vk_peer_id=peer_id)
                session.add(chat)
                await session.commit()

        return chat

    async def get_by_peer(self, peer_id: int) -> GameModel:
        """возвращает gamemodel по peer_id из vk.
        если такой игры нет в базе, создает неактивную"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = (
                    select(GameModel)
                    .join(ChatModel, GameModel.chat_id == ChatModel.id)
                    .filter_by(vk_peer_id=peer_id)
                )
                result = await session.execute(q)
                game = result.scalars().first()

                if not game:
                    game = await self.create_game(peer_id)

        return game

    async def change_state(self, game_id: int, new_state: str) -> None:
        """смена статуса игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = update(GameModel).filter_by(id=game_id).values(state=new_state)
                await session.execute(q)
