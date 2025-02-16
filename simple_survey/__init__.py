from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'simple_survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    #Name of the Participant
    Name = models.StringField(label="What is your name?")
    Age = models.IntegerField(label="What is your age?",min=13,max=125)
    Hair_color = models.StringField(
        label="What is your hair color?",
        choices=['Black', 'Green','White', 'White'],
    )
    pass


# PAGES
class Survey(Page):
    # player variables - so the relevant model is 'player'
    form_model = 'Player'

    #we specifically need the names6555
    form_fields = ['Name','Age','Hair_color']
    pass

class Results(Page):
    pass


page_sequence = [Survey, Results]
