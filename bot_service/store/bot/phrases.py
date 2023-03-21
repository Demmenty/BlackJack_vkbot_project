class BotPhrase:
    """заготовленные общие фразы бота"""

    def meeting(again: bool = False) -> str:
        if again:
            phrase = (
                "Ваша команда натыкается на знакомую таверну-казино. %0A"
                "Бледная тень то ли улыбается вам, то ли скалится."
            )
        else:
            phrase = (
                "Ваша группа наткнулась на зловещего вида таверну.  %0A"
                "Изнутри доносится звон монет и призрачный хохот. "
                "Зайдя внутрь, вы обнаруживаете казино, в котором не занят только карточный стол."
            )
        return phrase

    def no_personal_chating() -> str:
        return f"Призрак не обращает на вас внимания. Одинокие путники ему не интересны."

    def vk_error(error_code: int) -> str:
        return "Завывания ветра глушат вас. Сегодня здесь бушует непогода..."