from app.base.base_accessor import BaseAccessor
from app.game.models import *


from app.game.models import VKUserModel

class GameAccessor(BaseAccessor):
    """тут будет взаимосвязь gamemanager и database"""
    ...


    async def get_or_create_vk_user(self, vk_user_id: int) -> VKUserModel:
        """возвращает VKUserModel, если нет - создает и возвращает.
        передать vk_user_id (это user_id из vk update)"""

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(VKUserModel).filter_by(vk_user_id=vk_user_id)
                result = await session.execute(q)
                vk_user = result.scalars().first()

                if not vk_user:
                    name = await self.app.store.vk_api.get_username(user_id=vk_user_id)
                    vk_user = VKUserModel(vk_peer_id=vk_user_id, name=name)
                    session.add(vk_user)
                    await session.commit()

        return vk_user
