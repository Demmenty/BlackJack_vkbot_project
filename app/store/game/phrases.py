from app.store.common.utils import get_noun_ending


class GamePhrase:
    """заготовленные фразы бота для игры"""

    def game_offer(self, again: bool = False) -> str:
        if again:
            return f"Тень предлагает провести еще раунд %0A"
        else:
            return f"Мрачная тень предлагает сыграть партию в Блек Джек %0A"

    def game_is_on(self) -> str:
        return "Парящая нежить шипит на вас, намекая не мешать игре"

    def game_is_off(self) -> str:
        return "Тень не понимает, чего вы хотите, ведь в данный момент никто не играет."

    def game_begun(self) -> str:
        return "Злорадно хохоча, ваш странный дилер, перемешивает огромную кипу карт %0A"

    def wait_players(self) -> str:
        return "Нетерпеливо постукивая по столу, тень ожидает, когда игроки займут свои места."

    def game_aborted(self, name: str = None) -> str:
        phrase = "Призрак недовольно убирает карты и теряет к вам интерес. %0A"
        if name:
            phrase += (
                f"При этом {name} удостаивается полного ненависти взгляда."
            )
        return phrase

    def game_canceled(self, name: str) -> str:
        return (
            f"Угрожая святой водой, {name} заставляет тень немедленно закончить игру.%0A"
            "Пораженный такой наглостью, призрачный дилер всё же подчиняется."
        )

    def rules(self, name) -> str:
        rules = (
            "Черные бездны на месте глаз призрака расширяются от удивления,"
            " что кто-то не знаком со столь популярной в этих краях игрой. "
            f"Тем не менее, {name} слышит хорошо заученную речь:  %0A"
            "- игроки до раздачи карт делают ставки, называя сумму монет или выбирая из распространенных вариантов%0A"
            "- дилер, то есть я, раздает игрокам по две карты%0A"
            "- вы можете попросить еще карту по желанию%0A"
            "- цель - набрать очков больше, чем у меня%0A"
            "- но есть вы наберете больше 21, сразу проигрываете свою душу, то есть, кхм, монеты%0A"
            "Как считать очки? Очень просто, даже вы разберетесь:  %0A"
            "- карты с числом так и считаются%0A"
            "- валет, дама, король - как 10%0A"
            "- туз особенный: 11 если набранные очки не больше 21, иначе - 1%0A"
            "Этих знаний вам будет достаточно."
        )

        return rules

    def no_players(self) -> str:
        return "Тень печально обводит взором пустой стол. Вам её даже жалко."

    def player_registered(self, name: str) -> str:
        return f"{name} усаживается за стол."

    def player_unregistered(self, name: str) -> str:
        return f"{name} не желает соглашаться на эту авантюру."

    def player_already_registered(self, name: str) -> str:
        return f"{name} нетерпеливо ерзает за игровым столом."

    def active_players(self, players: list[str]) -> str:
        if len(players) == 1:
            player = players[0]
            phrase = (
                f"В самоуверенном одиночестве за столом обнаруживается {player}"
            )
        elif len(players) == 2:
            players = " и ".join(players)
            phrase = f"{players} решили испытать удачу."
        else:
            players = " и ".join(players[:-1]) + " и " + players[-1]
            phrase = f"{players} собрались за столом в ожидании игры."
        return phrase

    def waiting_bets(self) -> str:
        return (
            f"Потусторонний дилер потирает конечности в ожидании ваших золотых."
        )

    def show_cash(self, name: str, cash: int) -> str:
        cash_string = get_noun_ending(
            cash, "золотая монета", "золотые монеты", "золотых монет"
        )
        if cash < 100:
            phrase = f"{name} заглядывает в потрепанный кошелек, наскребая {cash_string}"
        elif cash > 3000:
            phrase = (
                f"{name} вывалиает свой увесистый кошель на стол. "
                + f"Проходит немало времени, пока {name} наконец не заявляет довольно: {cash_string}"
            )
        elif cash == 300:
            phrase = (
                f"{name} заглядывает в кошелек и видит там три сотни золотых.%0A"
                + f"Вдалеке слышится жуткий мужской крик, но никто не придает этому значения."
            )
        else:
            phrase = (
                f"Заглядывая в карман, {name} обнаруживает там {cash_string}"
            )
        return phrase

    def no_cash(self, name: str) -> str:
        return f"{name} хочет сесть за стол, но понимает, что больше ставить нечего."

    def to_much_bet(self, name: str) -> str:
        return f"{name} понял, что монет для желаемой ставки недостаточно и размышляет над другой суммой."

    def bet_accepted(self, name: str, bet: int) -> str:
        if bet < 51:
            bet_string = get_noun_ending(bet, "монету", "монеты", "монет")
            phrase = (
                f"{name} кропотливо отсчитывает жалкие {bet_string} и кладет на стол. "
                + "Во взгляде тени промелькнула нехорошая искра."
            )
        elif bet > 499:
            bet_string = get_noun_ending(bet, "монеты", "монет", "монет")
            phrase = (
                f"Внушительная гора из {bet_string} образовалась на столе.%0A"
                + "{name} получает одобрительный кивок призрака."
            )
        else:
            bet_string = get_noun_ending(bet, "монету", "монеты", "монет")
            phrase = f"{name} ставит {bet_string}."
        return phrase

    def bet_accepted_already(self, name: str, bet: int) -> str:
        bet_string = get_noun_ending(bet, "монету", "монеты", "монет")
        phrase = (
            f"{name} тянется, чтобы сделать ставку, но в это мгновение понимает, что уже положил {bet_string}. "
            + f"Одергивая руку, {name} надется, что никто не заметил такой глупости."
        )
        return phrase

    def not_a_player(self, name: str) -> str:
        return f"{name} получает от тени угрозу вышвыривания из таверны, если не перестанет мешать игре"

    def zero_bet(self, name: str) -> str:
        return (
            f"{name}, вы всерьез полагали, что загробный дилер не заметит отсутствия вашей ставки? "
            "Стоит положить хоть немного монет, иначе мертвые вам позавидуют."
        )

    def no_bet(self, name: str) -> str:
        return f"Таверна затихла в тревожном ожидании. Если вы {name}, лучше бы вам опомниться."

    def wrong_state(self) -> str:
        return "Тень недоумевающе покорежилась."

    def dealing_started(self) -> str:
        return (
            "Неживой дилер принялся ловко раздавать карты. "
            "За её движениями невозможно уследить."
        )

    def player_turn(self, name: str) -> str:
        return f"Карты полетели в сторону авантюриста по имени {name}."

    def not_your_turn(self, name: str) -> str:
        return f"{name} пытается встрять без очереди, но тень игнорирует такое нахальство"

    def cards_received(self, cards: list[str]) -> str:
        return f"Следующие карты появились перед игроком: " + " ".join(cards)

    def show_hand(self, name: str, cards: list[str]) -> str:
        if not cards:
            phrase = f"{name} смотрит в пустоту."
        else:
            phrase = f"{name} смотрит на карты перед собой: %0A" + " ".join(
                cards
            )
        return phrase

    def offer_a_card(self) -> str:
        return f"Тень сообщает, что можно взять еще карту"

    def blackjack(self, name: str) -> str:
        return f"{name} радуется, видя выпавший Блек Джек."

    def overflow(self) -> str:
        return f"Перебор!"

    def player_loss(self, name: str) -> str:
        return f"{name} печально наблюдает, как монеты растворяется в воздухе"

    def player_draw(self, name: str) -> str:
        return f'"С вами у нас ничья, {name}", заявляет призрак.'

    def player_win(self, name: str, blackjack: bool = False) -> str:
        if blackjack:
            phrase = f"{name} выигрывает и получает ставку в полуторном размере! Остальные игроки не скрывают зависти."
        else:
            phrase = (
                f"{name} ощущает сладкий вкус победы и утяжеление кошелька."
            )
        return phrase

    def deal_to_deale(self) -> str:
        return f"Тень начинает раздавать карты себе."

    def game_ended(self) -> str:
        return f"Раунд окончен. Призрак недобро хохочет."
