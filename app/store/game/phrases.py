from app.store.common.utils import get_noun_ending


class GamePhrase:
    """заготовленные фразы бота для игры"""

    def game_offer(again: bool = False) -> str:
        if again:
            return f"Тень настойчиво предлагает продолжить игру. %0A"
        else:
            return (
                f"Мрачная сущность предлагает сыграть партию в Блек Джек. %0A"
            )

    def game_is_on() -> str:
        return "Парящая нежить шипит на вас, намекая не мешать игре"

    def game_is_off() -> str:
        return "Тень не понимает, чего вы хотите, ведь в данный момент никто не играет."

    def game_begun() -> str:
        return "Злорадно смеясь, морок перемешивает огромную кипу карт. %0A"

    def wait_players() -> str:
        return "Нетерпеливо постукивая по столу, тень ожидает, когда игроки займут свои места."

    def game_aborted(name: str = "") -> str:
        phrase = "Призрак недовольно убирает карты и теряет к вам интерес. %0A"
        if name:
            phrase += (
                f"При этом {name} удостаивается полного ненависти взгляда."
            )
        return phrase

    def game_canceled(name: str) -> str:
        return (
            f"Угрожая святой водой, {name} заставляет тень немедленно закончить игру.%0A"
            "Пораженная такой наглостью нежить всё же подчиняется."
        )

    def rules(name: str) -> str:
        rules = (
            "Черные бездны на месте глаз призрака расширяются от удивления,"
            " что кто-то не знаком со столь популярной в этих краях игрой. %0A%0A"
            f"Тем не менее, {name} слышит хорошо заученную речь:  %0A"
            "- игроки до раздачи карт делают ставки, называя сумму монет или выбирая из распространенных вариантов%0A"
            "- дилер, то есть я, раздает игрокам по две карты%0A"
            "- вы можете попросить еще карту по желанию%0A"
            "- цель - набрать очков больше, чем у меня%0A"
            "- но если вы наберете больше 21, сразу проигрываете свою душу, то есть, кхм, монеты%0A %0A"
            "Как считать очки? Очень просто, даже вы разберетесь:  %0A"
            "- карты с числом так и считаются%0A"
            "- валет, дама, король - как 10%0A"
            "- туз особенный: 11 если все набранные очки не больше 21, иначе 1%0A"
            "Этих знаний вам будет достаточно, - добавляет тень."
        )

        return rules

    def all_play(losers: int) -> str:
        if not losers:
            return "Никто не остался в стороне, и игра начинается!"
        else:
            return "Все играют, отлично! %0A Из тех, у кого остались монеты, хихикающе добавляет тень."

    def all_losers() -> str:
        return "Зловеще смеясь, тень заявляет, что больше с вашей команды взять нечего и прогоняет из таверны."

    def no_players() -> str:
        return "Тень печально обводит взором пустой стол. Вам её даже жалко."

    def player_registered(name: str) -> str:
        return f"{name} усаживается за стол."

    def player_unregistered(name: str) -> str:
        return f"{name} не желает соглашаться на эту авантюру."

    def player_already_registered(name: str) -> str:
        return f"{name} нетерпеливо ёрзает на стуле."

    def active_players(players: list[str]) -> str:
        if len(players) == 1:
            player = players[0]
            phrase = f"В гордом одиночестве за столом обнаруживается {player}."
        elif len(players) == 2:
            players = " и ".join(players)
            phrase = f"{players} решили испытать удачу."
        else:
            players = " и ".join(players[:-1]) + " и " + players[-1]
            phrase = f"{players} собрались за столом в ожидании игры."
        return phrase

    def waiting_bets() -> str:
        return "Потусторонний дилер потирает конечности в ожидании золотых."

    def show_cash(name: str, cash: int) -> str:
        cash_string = (
            str(cash)
            + " "
            + get_noun_ending(
                cash, "золотая монета", "золотые монеты", "золотых монет"
            )
        )
        if cash == 0:
            phrase = f"{name} чувствует гнетущую пустоту своего кошелька, и, кажется, чего-то еще."
        elif cash < 100:
            phrase = f"{name} заглядывает в потрепанный кошелек, наскребая {cash_string}."
        elif cash > 3000:
            phrase = (
                f"{name} вываливает свой увесистый кошель на стол. "
                + f"Проходит немало времени, пока {name} наконец не заявляет довольно: {cash_string}"
            )
        elif cash == 300:
            phrase = (
                f"{name} заглядывает в кошелек и видит там три сотни золотых.%0A"
                + f"Вдалеке слышится жуткий мужской крик, но никто не придает этому значения."
            )
        else:
            phrase = (
                f"Заглядывая в карман, {name} обнаруживает там {cash_string}."
            )
        return phrase

    def no_cash_to_play(name: str) -> str:
        return f"{name} хочет сесть за стол, но понимает, что больше ставить нечего."

    def last_cash_spent(name: str, sex: str) -> str:
        if sex == "female":
            phrase = (
                f"{name} потратила последние монеты, и вы обращаете внимание, "
                + "что в глазницах тени вспыхнул фиолетовый свет."
            )
        else:
            phrase = (
                f"{name} удрученно осознает потерю последних золотых. "
                + " Неприятное холодное дуновение прошлось по вашим ногам."
            )
        return phrase

    def to_much_bet(name: str) -> str:
        return f"{name} осознает, что монет для желаемой ставки недостаточно и размышляет над другой суммой."

    def bet_accepted(name: str, bet: int) -> str:
        if bet == 1:
            phrase = f"{name} с невозмутимым видом кидает единственную монету и получает осуждающие взгляды."
        elif bet < 51:
            bet_string = (
                str(bet)
                + " "
                + get_noun_ending(bet, "монету", "монеты", "монет")
            )
            phrase = (
                f"{name} кропотливо отсчитывает жалкие {bet_string} и кладет на стол. "
                + "Во взгляде тени промелькнула нехорошая искра."
            )
        elif bet > 499:
            bet_string = (
                str(bet)
                + " "
                + get_noun_ending(bet, "монеты", "монет", "монет")
            )
            phrase = (
                f"Внушительная гора из {bet_string} образовалась на столе.%0A"
                + f"{name} получает одобрительный кивок призрака."
            )
        else:
            bet_string = (
                str(bet)
                + " "
                + get_noun_ending(bet, "монету", "монеты", "монет")
            )
            phrase = f"{name} ставит {bet_string}."
        return phrase

    def bet_accepted_already(name: str, bet: int, sex: str) -> str:
        bet_string = (
            str(bet) + " " + get_noun_ending(bet, "монету", "монеты", "монет")
        )
        if sex == "male":
            phrase = (
                f"{name} тянется, чтобы сделать ставку, "
                + f"но в это мгновение понимает, что уже положил {bet_string}. "
                + f"Одергивая руку, {name} надется, что никто не заметил такой глупости."
            )
        if sex == "female":
            phrase = (
                f"{name} попыталась незаметно изменить свою ставку, но не прошла проверку ловкости. "
                + f"На столе остались лежать {bet_string}."
            )
        return phrase

    def not_a_player(name: str) -> str:
        return f"{name} получает от тени угрозу вышвыривания из таверны, если не перестанет мешать игре"

    def not_a_player_cash(name: str) -> str:
        return (
            f"{name} задумчиво вглядывается в зияющую пропасть своих карманов."
        )

    def zero_bet(name: str) -> str:
        return (
            f"{name}, вы всерьез полагали, что зоркий дилер не заметит отсутствия вашей ставки? "
            "Стоит положить хоть немного монет, иначе мертвые вам позавидуют."
        )

    def no_player_bet(name: str) -> str:
        return f"Ударом высокоточного вихря {name} вышвыривается из-за стола."

    def all_bets_placed() -> str:
        return "Зловеще улыбаясь, тень объявляет, что все ставки сделаны."

    def wrong_state() -> str:
        return "Тень недоумевающе покорежилась."

    def dealing_started() -> str:
        return (
            "Нежить принялась ловко раздавать карты. "
            "За её движениями невозможно уследить."
        )

    def player_turn(name: str, sex: str) -> str:
        if sex == "female":
            return f"По летящим в нее картам, {name} догадалась, что наступил ее ход."
        if sex == "male":
            return f"{name} слышит, что объявлен его ход."

    def not_your_turn(name: str) -> str:
        return f"{name} пытается встрять без очереди, но тень игнорирует такое нахальство."

    def cards_received(cards: list[str]) -> str:
        return f"Следующие карты появились на столе: %0A" + " ".join(cards)

    def show_hand(name: str, cards: list[str]) -> str:
        if not cards:
            phrase = f"{name} смотрит в пустоту."
        else:
            phrase = f"{name} смотрит на карты перед собой: %0A" + " ".join(
                cards
            )
        return phrase

    def offer_a_card(name: str) -> str:
        return f"Тень выжидательно уставилась. %0AКакой выбор сделает {name} ?"

    def no_player_card_move(name: str, sex: str) -> str:
        if sex == "female":
            return f"{name} долго думала, и тень отворачивается от неё."
        if sex == "male":
            return f"{name} погружен в себя, его молчание расценено как желание остановиться."

    def blackjack(name: str) -> str:
        return f"{name} радуется, видя выпавший Блек Джек."

    def overflow() -> str:
        return f"Перебор!"

    def player_loss(name: str) -> str:
        return f"{name} печально наблюдает, как монеты растворяются в воздухе."

    def player_draw(name: str) -> str:
        return f'"С вами у нас ничья, {name}", заявляет призрак.'

    def player_win(name: str, blackjack: bool = False) -> str:
        if blackjack:
            phrase = f"{name} выигрывает и получает ставку в полуторном размере! Все присутствующие не скрывают зависти."
        else:
            phrase = (
                f"{name} ощущает сладкий вкус победы и утяжеление кошелька."
            )
        return phrase

    def deal_to_dealer() -> str:
        return f"Призрак дилера начинает раздавать себе."

    def game_ended() -> str:
        return f"Раунд окончен."

    def start_cash_given(name: str, start_cash: int) -> str:
        start_cash_string = (
            str(start_cash)
            + " "
            + get_noun_ending(
                start_cash, "золотая монета", "золотые монеты", "золотых монет"
            )
        )
        phrase = (
            "Видя ваши дырявые карманы, призрак тяжело вздыхает.%0A"
            + f"{name} вдруг обнаруживает у себя кошелек, в котором сверкает {start_cash_string}."
        )
        return phrase

    def chat_stat(games_played: int, casino_cash: int) -> str:
        if games_played == 0:
            games_played_string = "Тень укоризненно сообщает, что вы пока ни разу не сыграли с ней."
            casino_cash_string = "Банк казино пустует."
            return games_played_string + "%0A" + casino_cash_string

        games_played_string = (
            str(games_played)
            + " "
            + get_noun_ending(
                games_played,
                "игра проведена в казино.",
                "игры сыграны.",
                "игр уже проведено в этой таверне.",
            )
        )
        if casino_cash == 0:
            casino_cash_string = "На счету казино пусто."
        if casino_cash < 0:
            casino_cash_string = (
                f"В бюджете казино образовался долг в {abs(casino_cash)} "
                + get_noun_ending(
                    casino_cash, "монету.", "золотых монеты.", "золотых монет."
                )
            )
        else:
            casino_cash_string = (
                f"Казино обогатилось на {casino_cash} "
                + get_noun_ending(
                    casino_cash, "монету.", "золотых монеты.", "золотых монет."
                )
            )

        return games_played_string + "%0A" + casino_cash_string

    def player_stat(
        name: str,
        sex: str,
        games_played: int,
        games_won: int,
        games_lost: int,
        cash: int,
    ) -> str:
        if games_played == 0:
            if sex == "female":
                return f"{name} тени не знакома, и она ничего не может о ней сказать."
            else:
                return f"{name} тени не знаком, и она ничего не может о нем сказать."

        games_played_string = (
            str(games_played)
            + " "
            + get_noun_ending(games_played, "игру", "игры", "игр")
        )
        cash_string = (
            str(cash)
            + " "
            + get_noun_ending(
                cash, "золотой", "золотых монеты", "золотых монет"
            )
        )

        if sex == "female":
            phrase = f"{name} сыграла {games_played_string}.%0A"
            phrase += f"Проиграно {games_lost}, выиграно {games_won}.%0A"
            phrase += f"У нее в кошельке {cash_string}."
        else:
            phrase = f"{name} сыграл {games_played_string}.%0A"
            phrase += f"Проиграно {games_lost}, выиграно {games_won}.%0A"
            phrase += f"У него в кошельке {cash_string}."

        return phrase

    def bot_leaving() -> str:
        return "Очертания тени внезапно начали растворяться в окружении, и вскоре она совсем исчезла..."

    def bot_returning() -> str:
        return (
            "Призрачный силует появляется из небытия:%0A"
            " - прошу прощения, моя связь с миром смертных слаба, на чем мы остановились?..."
        )

    def get_restore_command(name: str, sex: str) -> str:
        phrase = f"{name} внезапно вспоминает о заклятии, спасающем в критических ситуациях.%0A"
        if sex == "female":
            phrase += "Но она плохо помнит, как оно звучало... "
        else:
            phrase += "Он не сразу вспоминает, как оно звучало... "
        phrase += "convici stultus, converta tempus... condemna alea..."

        return phrase

    def cash_restored() -> str:
        return (
            "Пространство начало искажаться, и вашу группу затягивает в область между реальностями.%0A"
            "После избавления от содержимого желудков и прихода в себя, "
            "вы обнаруживаете себя при входе в таверну с карманами, полными золотых. "
            "Кажется, призрак даже не обратил на произошедшее внимания..."
        )
