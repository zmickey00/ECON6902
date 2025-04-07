from otree.api import *


doc = """
Consent Form
"""


class C(BaseConstants):
    NAME_IN_URL = 'consent'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    playerid = models.StringField(label="Please provide your Player ID")
    consent = models.BooleanField(default=0)

    pass


# PAGES
class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']
    @staticmethod
    def before_next_page(player, timeout_happened):

        player.participant.label = player.field_maybe_none('playerid')
    pass

class Loading(Page):
    timeout_seconds = 1

class No_Consent(Page):
    @staticmethod
    def is_displayed(player):
        return player.consent == 0
class Instructions(Page):
    pass
class Results(Page):
    pass
class Stock_Price_Display(Page):
    pass


page_sequence = [Consent, No_Consent, Instructions, Stock_Price_Display]
