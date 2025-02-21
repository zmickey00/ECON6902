from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'publicgood'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3

    MULTIPLIER = 3
    ENDOWMENT = 10
class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_investment = models.FloatField(initial=0)


class Player(BasePlayer):
    investment = models.FloatField(label="How many points do you want to invest?",min=0, max=C.ENDOWMENT)

def set_payoffs(group :Group):

    players = group.get_players()

    for p in players:
        group.total_investment = group.total_investment + p.investment

    for p in players:
        p.payoff = C.ENDOWMENT - p.investment + group.total_investment * C.MULTIPLIER/C.PLAYERS_PER_GROUP
# PAGES
class Instructions(Page):

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Invest(Page):
    form_model = 'player'
    form_fields = ['investment']
    pass

class ResultsWaitPage(WaitPage):

    after_all_players_arrive = set_payoffs


class Results(Page):

    pass


page_sequence = [Instructions, Invest, ResultsWaitPage, Results]
