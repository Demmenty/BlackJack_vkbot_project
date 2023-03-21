def get_noun_ending(number: int, one: str, two: str, five: str) -> str:
    """возвращает вариант слова с правильным окончанием в зависимости от числа
    Нужно передать число и соответствующие варианты
    например: get_noun_ending(4, 'слон', 'слона', 'слонов'))
    """
    n = abs(number)
    n %= 100
    if 20 >= n >= 5:
        return five
    n %= 10
    if n == 1:
        return one
    if 4 >= n >= 2:
        return two
    return five
