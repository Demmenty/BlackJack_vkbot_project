from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.store.database.sqlalchemy_base import db


class PeerModel(db):
    __tablename__ = "peer"

    id = Column(Integer, primary_key=True)
    vk_peer_id = Column(Integer, unique=True, nullable=False)

    def __repr__(self):
        return f"PeerModel(id={self.id!r}, vk_peer_id={self.vk_peer_id!r})"


# TODO ограничить варианты state: inactive, define_players, betting, ...
class GameModel(db):
    __tablename__ = "game"

    id = Column(Integer, primary_key=True)
    peer_id = Column(ForeignKey("peer.id", ondelete="CASCADE"), nullable=False)
    state = Column(String, default="inactive", nullable=False)

    def __repr__(self):
        return f"GameModel(id={self.id!r}, state={self.state!r})"


class PlayerModel(db):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(ForeignKey("game.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"PlayerModel(id={self.id!r})"
    

class UserModel(db):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    vk_user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

    def __repr__(self):
        return f"UserModel(id={self.id!r}, name={self.name!r})"
