from otree.api import *
import random

doc = """
Stock market investment game with hardcoded trends
"""


class Constants(BaseConstants):
    name_in_url = 'invest_game'
    players_per_group = None
    num_rounds = 1
    initial_endowment = 10
    num_ticks = 20

    TREND_DATA = {
        'trend1': [10.0, 9.7, 10.6, 10.7, 12.6, 11.9, 13.4, 14.3, 13.6, 14.1,
                   15.4, 16.1, 16.6, 15.9, 16.2, 16.7, 17.2, 19.1, 19.4, 19.9, 19.2],
        'trend2': [10.0, 10.2, 10.5, 10.8, 11.1, 11.4, 11.7, 12.0, 12.3, 12.6,
                   12.9, 13.2, 13.5, 13.8, 14.1, 14.4, 14.7, 15.0, 15.3, 15.6, 15.9],
        'trend3': [10.0, 9.8, 9.6, 9.4, 9.2, 9.0, 8.8, 8.6, 8.4, 8.2,
                   8.0, 7.8, 7.6, 7.4, 7.2, 7.0, 6.8, 6.6, 6.4, 6.2, 6.0],
        'trend4': [10.0, 10.5, 9.5, 10.0, 10.5, 9.5, 10.0, 10.5, 9.5, 10.0,
                   10.5, 9.5, 10.0, 10.5, 9.5, 10.0, 10.5, 9.5, 10.0, 10.5, 9.5],
        'trend5': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0,
                   20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0],
        'trend6': [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0,
                   0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    investment = models.FloatField(
        min=0,
        label="How much do you want to invest?",
        doc="Amount player chooses to invest"
    )

    def current_trend_name(self):
        participant = self.participant
        if 'assigned_trends' in participant.vars:
            trend_idx = participant.vars.get('current_trend_idx', 0)
            return f"Trend {trend_idx + 1}"
        return ""

    def current_prices(self):
        participant = self.participant
        if 'assigned_trends' in participant.vars:
            trend_idx = participant.vars.get('current_trend_idx', 0)
            trend_key = participant.vars['assigned_trends'][trend_idx]
            return Constants.TREND_DATA[trend_key]
        return []

    def available_balance(self):
        participant = self.participant
        tick = participant.vars.get('current_tick', 0)
        prices = self.current_prices()

        if tick == 0:
            return float(participant.vars.get('cash', Constants.initial_endowment))

        if tick > 0 and len(prices) > tick:
            prev_price = prices[tick - 1]
            curr_price = prices[tick]
            invested = participant.vars.get('invested', 0)
            cash = participant.vars.get('cash', Constants.initial_endowment)
            return cash + (invested * (curr_price / prev_price))

        return float(participant.vars.get('cash', Constants.initial_endowment))


class InvestmentPage(Page):
    form_model = 'player'
    form_fields = ['investment']

    @staticmethod
    def is_displayed(player):
        participant = player.participant
        if 'assigned_trends' not in participant.vars:
            participant.vars['assigned_trends'] = random.sample(
                list(Constants.TREND_DATA.keys()),
                random.choice([3, 4])
            )
            participant.vars['current_trend_idx'] = 0
            participant.vars['current_tick'] = 0
            participant.vars['cash'] = float(Constants.initial_endowment)
            participant.vars['invested'] = 0.0

        return (
                participant.vars['current_trend_idx'] < len(participant.vars['assigned_trends']) and
                participant.vars['current_tick'] < Constants.num_ticks
        )

    def vars_for_template(player):
        participant = player.participant
        prices = player.current_prices()
        current_tick = participant.vars['current_tick']

        return {
            'current_tick': current_tick + 1,
            'total_ticks': Constants.num_ticks,
            'trend_name': player.current_trend_name(),
            'current_price': f"{prices[current_tick]:.2f}" if current_tick < len(prices) else "0.00",
            'available_balance': f"{player.available_balance():.2f}"
        }

    def before_next_page(player, timeout_happened):
        participant = player.participant
        prices = player.current_prices()
        current_tick = participant.vars['current_tick']

        # Update investment value
        if current_tick > 0 and len(prices) > current_tick:
            prev_price = prices[current_tick - 1]
            curr_price = prices[current_tick]
            participant.vars['invested'] *= (curr_price / prev_price)

        participant.vars['cash'] = player.available_balance() - player.investment
        participant.vars['invested'] = float(player.investment)
        participant.vars['current_tick'] += 1

        # Reset for new trend
        if participant.vars['current_tick'] >= Constants.num_ticks:
            participant.vars['current_trend_idx'] += 1
            participant.vars['current_tick'] = 0
            participant.vars['cash'] = float(Constants.initial_endowment)
            participant.vars['invested'] = 0.0


class Results(Page):
    @staticmethod
    def is_displayed(player):
        participant = player.participant
        return (
                'assigned_trends' in participant.vars and
                participant.vars['current_trend_idx'] >= len(participant.vars['assigned_trends'])
        )


page_sequence = [InvestmentPage, Results]