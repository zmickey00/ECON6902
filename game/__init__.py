from otree.api import *

class Constants(BaseConstants):
    name_in_url = 'investment_game'
    players_per_group = None
    num_rounds = 5
    initial_balance = Currency(10)
    trend = [[1, 2, 3], [4, 5, 6]]
    # trends are no longer used in this version

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Player's available funds.
    balance = models.CurrencyField(
        initial=Constants.initial_balance,
        doc="Player's current balance"
    )
    # Funds invested into the market.
    investment_account = models.CurrencyField(
        initial=0,
        doc="Amount invested into the market"
    )
    # Investment decision: positive for investing, negative for withdrawing.
    investment = models.CurrencyField(
        # These static min/max values are only used for round 1,
        # but we override validation dynamically in the page.
        min=-Constants.initial_balance,
        max=Constants.initial_balance,
        doc="Amount to invest (positive) or withdraw (negative)",
        label="Investment amount (or withdrawal if negative)"
    )

class Investment(Page):
    form_model = 'player'
    form_fields = ['investment']

    @staticmethod
    def vars_for_template(player: Player):
        # For round 1, set the starting values.
        if player.round_number == 1:
            player.balance = Constants.initial_balance
            player.investment_account = 0
        else:
            # Use previous round's values.
            prev = player.in_round(player.round_number - 1)
            player.balance = prev.balance - prev.investment
            player.investment_account = prev.investment_account + prev.investment

        return {
            'current_balance': player.balance,
            'current_investment_account': player.investment_account,
            'round_number': player.round_number,
        }

class Growth(Page):
    class Growth(Page):
        @staticmethod
        def before_next_page(player: Player, timeout_happened):
            # Multiply the current investment account by 2
            player.investment_account = player.investment_account * 2

    pass


page_sequence = [Investment, Growth]
