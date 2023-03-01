from sqlalchemy import select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import ChatModel, GameModel


class GameAccessor(BaseAccessor):
    """взаимосвязь gamemanager и database"""

    async def get_or_create_game(self, chat_id: int) -> GameModel:
        """возвращает GameModel, если нет - создает неактивную
        передать chat_id (это peer_id из vk)"""

        chat = await self.get_or_create_chat(vk_peer_id=chat_id)

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

    async def get_game_by_chat(self, chat_id: int) -> GameModel | None:
        """возвращает GameModel по chat_id (peer_id из vk) или None"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(GameModel).filter(GameModel.chat.has(vk_peer_id=chat_id))
                result = await session.execute(q)
                game = result.scalars().first()
 
        return game

    async def is_game_on(self, chat_id: int) -> bool:
        """предикат, проверяющий, игра в процессе в данном чате или нет.
        chat_id = peer_id из vk"""

        game = await self.get_game_by_chat(chat_id=chat_id)

        if not game:
            return False

        # TODO убрать магические стринги
        if game.state == "inactive":
            return False

        return True

    async def change_game_state(self, game_id: int, new_state: str) -> None:
        """смена статуса игры"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = update(GameModel).filter_by(id=game_id).values(state=new_state)
                await session.execute(q)
