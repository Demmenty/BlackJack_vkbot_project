class BotPhrase:
    """заготовленные общие фразы бота"""

    def pm_msg(self) -> str:
        return f"Призрак не обращает на вас внимания. Одинокие путники ему не интересны."

    def meeting(self, again: bool = False) -> str:
        if again:
            phrase = (
                "Ваша команда натыкается на знакомую таверну-казино."
                "Бледная тень то ли улыбается вам, то ли скалится."
            )
        else:
            phrase = (
                "Ваша группа наткнулась на зловещего вида таверну."
                "Изнутри доносится звон монет и призрачный хохот."
                "Зайдя внутрь, вы обнаруживаете казино, в котором не занят только карточный стол."
            )
        return phrase
