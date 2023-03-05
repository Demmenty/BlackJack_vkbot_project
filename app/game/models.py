from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


class ChatModel(db):
    __tablename__ = "chat"

    id = Column(Integer, primary_key=True)
    vk_peer_id = Column(Integer, unique=True, nullable=False)

    # один_чат = одна_игра
    game = relationship(
        "GameModel",
        back_populates="chat",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"ChatModel(id={self.id!r}, vk_peer_id={self.vk_peer_id!r})"


# TODO ограничить варианты state: inactive, define_players, betting, dealing, petting, ...
# TODO загуглить, почему у меня связь отображается не как 1-1 и исправить
class GameModel(db):
    __tablename__ = "game"

    id = Column(Integer, primary_key=True)
    chat_id = Column(ForeignKey("chat.id", ondelete="CASCADE"), nullable=False)
    state = Column(String, default="inactive", nullable=False)
    current_player_id = Column(Integer, nullable=True)
    dealer_points = Column(Integer, nullable=True)

    chat = relationship(
        "ChatModel",
        back_populates="game",
        cascade="all, delete",
        passive_deletes=True,
    )
    players = relationship(
        "PlayerModel",
        back_populates="game",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"GameModel(id={self.id!r}, state={self.state!r})"


class PlayerModel(db):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("vk_user.id"), nullable=False)
    game_id = Column(ForeignKey("game.id", ondelete="CASCADE"), nullable=False)
    cash = Column(Integer, default=1000, nullable=False)
    bet = Column(Integer, nullable=True)
    hand: dict = Column(JSON, default={"cards": []}, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    game = relationship("GameModel", back_populates="players")
    vk_user = relationship("VKUserModel", back_populates="players")

    def __repr__(self):
        return f"PlayerModel(id={self.id!r})"


class VKUserModel(db):
    __tablename__ = "vk_user"

    id = Column(Integer, primary_key=True)
    vk_user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

    players = relationship("PlayerModel", back_populates="vk_user")

    def __repr__(self):
        return f"VKUserModel(id={self.id!r}, name={self.name!r})"


# TODO статистика, сколько всего денег выиграло казино
