import json
from dataclasses import asdict, dataclass


# событие от вк
@dataclass
class Update:
    id: int
    type: str
    from_id: int
    peer_id: int
    action_type: str = ""
    text: str = ""

    @property
    def json(self):
        return json.dumps(asdict(self))
