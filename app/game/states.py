import enum


class GameState(enum.Enum):
    """стадии игры в Black Jack"""

    inactive = "inactive"
    gathering = "gathering_players"
    betting = "betting"
    dealing = "dealing"
    results = "sum_up_results"
