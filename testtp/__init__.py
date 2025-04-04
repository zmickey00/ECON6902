from otree.api import *
import random
import json
import pandas as pd
import os

doc = """
Investment decision experiment with varying information disclosure and presentation formats
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_stock_prices():
    try:
        data_path = os.path.join(BASE_DIR, 'data.csv')
        df = pd.read_csv(data_path)
        prices = df['ObservedPrice'][1:].round(2).tolist()
            
        return prices
    except Exception as e:
        print(f"Error loading stock prices from CSV: {e}")
        return [9.9, 8.6, 10.1, 9.6, 10.1, 11.8, 11.9, 11.2, 12.1, 12.4, 
                13.9, 12.4, 13.1, 12.8, 11.1, 11.6, 11.1, 9.6, 9.9, 8.4]


class Constants(BaseConstants):
    name_in_url = 'investment_decisions'
    players_per_group = None
    num_rounds = 20
    initial_endowment = cu(10)
    
    stock_prices = get_stock_prices()
    
    disclosure_period = 3
    disclosure_rounds = list(range(1, num_rounds + 1, disclosure_period))


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    if subsession.round_number == 1:
        players = subsession.get_players()
        num_players = len(players)
        
        participants_per_group = (num_players + 3) // 4
        
        # 1: High frequency, numeric
        # 2: High frequency, visualized
        # 3: Low frequency, numeric
        # 4: Low frequency, visualized
        treatment_groups = []
        for group_id in range(1, 5):
            treatment_groups.extend([group_id] * participants_per_group)
            
        treatment_groups = treatment_groups[:num_players]
        random.shuffle(treatment_groups)
        
        for i, player in enumerate(players):
            player.treatment_group = treatment_groups[i]
            
            player.high_frequency = player.treatment_group in [1, 2]
            player.visualized = player.treatment_group in [2, 4]
            
            player.participant.vars['treatment_group'] = player.treatment_group
            player.participant.vars['high_frequency'] = player.high_frequency
            player.participant.vars['visualized'] = player.visualized
            player.participant.vars['stocks_owned'] = 0
            player.participant.vars['total_uninvested'] = 0
    
    else:
        for player in subsession.get_players():
            player.treatment_group = player.participant.vars['treatment_group']
            player.high_frequency = player.participant.vars['high_frequency']
            player.visualized = player.participant.vars['visualized']

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Treatment variables
    treatment_group = models.IntegerField()  # 1-4 representing the four conditions
    high_frequency = models.BooleanField()   # True for high frequency, False for low
    visualized = models.BooleanField()       # True for visualized, False for numeric only
    
    # Investment decision
    investment = models.CurrencyField(
        min=0, 
        max=Constants.initial_endowment,
        label="Investment amount"
    )
    
    # Remaining endowment (will be calculated automatically)
    remaining_endowment = models.CurrencyField()
    
    # Stocks purchased in this round
    stocks_purchased = models.FloatField()
    
    # Whether price was disclosed this round (for record keeping)
    price_disclosed = models.BooleanField()


# PAGES
class Introduction1(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        disclosure_rounds_text = ""
        for i, round_num in enumerate(Constants.disclosure_rounds):
            if i == 0:
                disclosure_rounds_text = str(round_num)
            elif i == len(Constants.disclosure_rounds) - 1:
                disclosure_rounds_text += " and " + str(round_num)
            else:
                disclosure_rounds_text += ", " + str(round_num)
        
        return {
            'high_frequency': player.high_frequency,
            'visualized': player.visualized,
            'disclosure_rounds': Constants.disclosure_rounds,
            'disclosure_rounds_text': disclosure_rounds_text
        }


class Investment(Page):
    form_model = 'player'
    form_fields = ['investment']
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        # Calculate remaining endowment
        player.remaining_endowment = Constants.initial_endowment - player.investment
        
        # Get stock price for this round
        current_price = Constants.stock_prices[player.round_number - 1]
        
        # Determine if price is disclosed this round
        if player.high_frequency:
            player.price_disclosed = True
        else:
            player.price_disclosed = player.round_number in Constants.disclosure_rounds
        
        # Calculate stocks purchased (even if price not known to participant)
        if player.investment > 0:
            player.stocks_purchased = float(player.investment) / current_price
        else:
            player.stocks_purchased = 0
            
        # Update participant vars for accumulated values
        player.participant.vars['stocks_owned'] += player.stocks_purchased
        player.participant.vars['total_uninvested'] += player.remaining_endowment
    
    @staticmethod
    def vars_for_template(player):
        # Get current and historical price information
        current_round = player.round_number
        current_price = Constants.stock_prices[current_round - 1]
        
        # Determine if price should be disclosed this round
        current_price_disclosed = True
        if not player.high_frequency:
            current_price_disclosed = current_round in Constants.disclosure_rounds
        
        # Create price history for display
        price_history = []
        for round_num in range(1, current_round + 1):
            # Determine if this historical price should be disclosed
            price_disclosed = True
            if not player.high_frequency:
                price_disclosed = round_num in Constants.disclosure_rounds
            
            if price_disclosed:
                price_display = f"${Constants.stock_prices[round_num - 1]}"
            else:
                price_display = "Not disclosed"
                
            # Include all rounds up to and including current round in history
            price_history.append((round_num, price_display))
        
        # For visualization, prepare data for JS
        prices = []
        rounds = []
        disclosed = []
        
        for r in range(1, current_round + 1):
            price = Constants.stock_prices[r - 1]
            is_disclosed = True if player.high_frequency else (r in Constants.disclosure_rounds)
            
            # Only include in visualization if disclosed
            if is_disclosed:
                prices.append(price)
                rounds.append(r)
                disclosed.append(True)
        
        return {
            'current_price': current_price,
            'current_price_disclosed': current_price_disclosed,
            'price_history': price_history,
            'prices_json': json.dumps(prices),
            'rounds_json': json.dumps(rounds),
            'disclosed_json': json.dumps(disclosed)
        }


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds
    
    @staticmethod
    def vars_for_template(player):
        # Get all players in all rounds
        all_players = player.in_all_rounds()
        
        # Prepare history data
        history = []
        for p in all_players:
            round_num = p.round_number
            price = Constants.stock_prices[round_num - 1]
            
            history.append({
                'round': round_num,
                'price': f"{price:.2f}",
                'disclosed': "Yes" if p.price_disclosed else "No",
                'investment': f"{p.investment:.2f}",
                'endowment': f"{p.remaining_endowment:.2f}",
                'stocks': f"{p.stocks_purchased:.4f}"
            })
        
        # Calculate final results
        total_stocks = player.participant.vars['stocks_owned']
        final_stock_price = Constants.stock_prices[-1]  # Last price
        stock_value = total_stocks * final_stock_price
        total_uninvested = player.participant.vars['total_uninvested']
        total_earnings = float(total_uninvested) + stock_value
        
        return {
            'history': history,
            'total_stocks': f"{total_stocks:.4f}",
            'final_stock_price': f"{final_stock_price:.2f}",
            'stock_value': f"{stock_value:.2f}",
            'total_uninvested': f"{total_uninvested:.2f}",
            'total_earnings': f"{total_earnings:.2f}"
        }


page_sequence = [Introduction1, Investment, Results]