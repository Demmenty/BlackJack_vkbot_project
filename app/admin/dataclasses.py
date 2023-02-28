from dataclasses import dataclass
from typing import Optional


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(id=session["admin"]["id"], email=session["admin"]["email"])
