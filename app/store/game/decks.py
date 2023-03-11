import random


class EndlessDeck:
    """бесконечная колода 52 карт для BlackJack"""

    card_values = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "Валет": 10,
        "Дама": 10,
        "Король": 10,
        "Туз": -1,
    }
    card_suits = ["♠", "♣", "♥", "♦"]

    def take_a_card(self) -> str:
        """возвращает одну случайную карту"""

        value = random.choice([key for key in self.card_values.keys()])
        suit = random.choice(self.card_suits)

        card = str(value) + " " + suit

        return card

    def count_points(self, cards: list[str]) -> int:
        """возвращает количество очков, соответствующее переданному списку карт"""

        points = 0
        aces = 0

        for card in cards:
            value = card.split()[0]
            weight = self.card_values.get(value)

            if weight != -1:
                points += weight
            else:
                aces += 1

        if not aces:
            return points

        for ace in range(aces):
            if (points + 11) > 21:
                points += 1
            else:
                points += 11

        return points

    def is_blackjack(self, cards: list[str]) -> bool:
        """проверяет на блекджек (2 карты = 21)"""

        result = len(cards) == 2 and self.count_points(cards) == 21

        return result

    # TODO метод возврата пути к картинке к нужной карте
