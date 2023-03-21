from hashlib import sha256

from sqlalchemy import Column, Integer, String

from store.database.sqlalchemy_base import db


class AdminModel(db):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)

    def is_password_valid(self, password: str) -> bool:
        return self.password == sha256(password.encode()).hexdigest()

    def __repr__(self):
        return f"AdminModel(id={self.id!r}, email={self.email!r})"
