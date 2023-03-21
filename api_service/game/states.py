from strenum import StrEnum


class GameState(StrEnum):
    """стадии игры в Black Jack"""

    inactive = "inactive"
    gathering = "gathering"
    betting = "betting"
    dealing_players = "dealing_players"
    dealing_dealer = "dealing_dealer"
    results = "results"
