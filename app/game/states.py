from enum import StrEnum


class GameState(StrEnum):
    """стадии игры в Black Jack"""

    inactive = "inactive"
    gathering = "gathering"
    betting = "betting"
    dealing = "dealing"
    results = "results"
