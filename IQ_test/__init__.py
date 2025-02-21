from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'IQ_test'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # # Name of the Participant
    # Name = models.StringField(label="What is your name?")
    # Age = models.IntegerField(label="What is your age?", min=13, max=125)
    # Hair_color = models.StringField(
    #     label="What is your hair color?",
    #     choices=['Black', 'Green', 'White', 'White'],
    # )
    IQ_Answer = models.IntegerField(label="What is your answer?")
    pass


# PAGES
class Survey(Page):
    # player variables - so the relevant model is 'player'
    form_model = 'player'

    # we specifically need the names6555
    form_fields = ['Name', 'Age', 'Hair_color']
    pass
class IQ(Page):
    form_model = 'player'

    form_fields = ['IQ_Answer']
    pass

class Results(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):

        if player.IQ_Answer == 15:
            player.payoff = player.payoff + 1000000

class Finished(Page):
    pass
page_sequence = [IQ, Results, Finished]
