from hashlib import sha256

from sqlalchemy import select

from app.admin.models import AdminModel
from app.base.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    async def get_by_email(self, email: str) -> AdminModel | None:

        async with self.app.database.session() as session:
            async with session.begin():
                q = select(AdminModel).filter_by(email=email)
                result = await session.execute(q)
                admin = result.scalars().first()

                return admin

    async def create_admin(self, email: str, password: str) -> None:

        async with self.app.database.session() as session:
            async with session.begin():
                # ищем админа
                q = select(AdminModel)
                result = await session.execute(q)
                admin = result.scalars().first()
                # если нет - создаем
                if not admin:
                    admin = AdminModel(
                        email=email,
                        password=sha256(password.encode("utf-8")).hexdigest(),
                    )
                    session.add(admin)
                    await session.commit()
