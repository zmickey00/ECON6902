from otree.api import *
import random
import json
import pandas as pd
import os

doc = """
Investment decision experiment with varying information disclosure and presentation formats.
Multiple sessions using different price data files.
"""

# Get the directory path of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to read stock prices from a CSV file
def get_stock_prices(session_num, num_rounds=20):
    try:
        # Construct the path to the data file - use the session number to choose the data file
        data_path = os.path.join(BASE_DIR, f'data{session_num}.csv')
        print(f"Reading data from: {data_path}")
        
        # Read CSV using pandas
        df = pd.read_csv(data_path)
        
        # Extract the 'ObservedPrice' column and round values to 2 decimal places
        prices = df['ObservedPrice'].round(2).tolist()
        
        # If the number of prices exceeds num_rounds+1, only take the first num_rounds+1 (including the final price)
        if len(prices) > num_rounds + 1:
            prices = prices[:num_rounds + 1]
            
        return prices
    except Exception as e:
        print(f"Error loading stock prices from CSV: {e}")
        # Use default prices in case of error
        # Add extra prices for final calculation
        return [10.5, 11.2, 9.8, 12.5, 13.0, 12.2, 11.5, 10.9, 12.8, 13.5, 
                14.0, 12.5, 11.8, 13.2, 14.5, 15.0, 14.2, 13.8, 15.5, 16.0, 16.5]


class Constants(BaseConstants):
    name_in_url = 'investment_decisions'
    players_per_group = None
    num_rounds = 80  # Total of 4 sessions, 20 rounds per session
    initial_endowment = cu(10)  # $10 initial fund in the first round
    
    # Each experiment uses a different data file
    num_sessions = 4  # Total of 4 experimental phases
    rounds_per_session = 20  # Number of rounds per session
    
    # Adjustable disclosure frequency
    # Disclosure period (e.g., 4 means disclose every 4 rounds)
    disclosure_period = 4
    
    # Wait time for the rest page (in seconds)
    rest_time = 8


class Subsession(BaseSubsession):
    session_num = models.IntegerField(initial=1)  # Indicates the current experimental phase number


def creating_session(subsession):
    # Set the session number
    session_round = (subsession.round_number - 1) // Constants.rounds_per_session + 1
    subsession.session_num = session_round
    
    print(f"Creating round {subsession.round_number}, session {session_round}")
    
    # Get the starting round for participant grouping
    is_first_round_of_session = ((subsession.round_number - 1) % Constants.rounds_per_session) == 0
    
    # For the first round, generate a random order of data files for each participant
    if subsession.round_number == 1:
        for player in subsession.get_players():
            # Generate a random order individually for each participant
            data_files = list(range(1, Constants.num_sessions + 1))  # [1, 2, 3, 4]
            random.shuffle(data_files)
            player.participant.vars['data_file_order'] = data_files
            print(f"Player {player.id_in_subsession}: data file order = {data_files}")
    
    # For the first round of the first experimental session, assign treatment groups
    if subsession.round_number == 1:
        # Get all participants
        players = subsession.get_players()
        num_players = len(players)
        
        # Calculate the number of participants per group (round up)
        participants_per_group = (num_players + 3) // 4  # Distribute participants as evenly as possible into 4 groups
        
        # Create a list for treatment group assignment
        # 1: High frequency, numeric
        # 2: High frequency, visualized
        # 3: Low frequency, numeric
        # 4: Low frequency, visualized
        treatment_groups = []
        for group_id in range(1, 5):
            treatment_groups.extend([group_id] * participants_per_group)
            
        # Truncate the list to match the actual number of participants
        treatment_groups = treatment_groups[:num_players]
        
        # Randomly shuffle the assignment order
        random.shuffle(treatment_groups)
        
        # Assign treatment groups
        for i, player in enumerate(players):
            player.treatment_group = treatment_groups[i]
            
            # Set frequency and visualization variables
            player.high_frequency = player.treatment_group in [1, 2]
            player.visualized = player.treatment_group in [2, 4]
            
            # Save to participant.vars to maintain consistency across rounds
            player.participant.vars['treatment_group'] = player.treatment_group
            player.participant.vars['high_frequency'] = player.high_frequency
            player.participant.vars['visualized'] = player.visualized
    
    # Initialize participant variables for the first round of each session
    if is_first_round_of_session:
        for player in subsession.get_players():
            # Copy treatment assignment (to maintain consistency)
            if subsession.round_number > 1:
                player.treatment_group = player.participant.vars['treatment_group']
                player.high_frequency = player.participant.vars['high_frequency']
                player.visualized = player.participant.vars['visualized']
            
            # Retrieve the current participant's data file order and the data file to be used for the current session
            data_file_order = player.participant.vars['data_file_order']
            current_data_file = data_file_order[session_round - 1]
            print(f"Player {player.id_in_subsession}, Session {session_round}: using data file {current_data_file}")
            player.participant.vars[f'current_data_file_{session_round}'] = current_data_file
            
            # Store the stock prices used for this session
            stock_prices = get_stock_prices(current_data_file, Constants.rounds_per_session)
            player.participant.vars[f'stock_prices_{session_round}'] = stock_prices
            
            # Reset funds and the last disclosure round
            player.participant.vars[f'current_funds_{session_round}'] = float(Constants.initial_endowment)
            player.participant.vars[f'last_disclosed_investment_{session_round}'] = 0.0
            player.participant.vars[f'last_disclosed_remaining_{session_round}'] = float(Constants.initial_endowment)
            player.participant.vars[f'last_disclosure_round_{session_round}'] = 1
    else:
        # For non-first round of the session, ensure treatment groups remain consistent
        for player in subsession.get_players():
            player.treatment_group = player.participant.vars['treatment_group']
            player.high_frequency = player.participant.vars['high_frequency']
            player.visualized = player.participant.vars['visualized']


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Treatment variables
    treatment_group = models.IntegerField()  # 1-4 represent the four conditions
    high_frequency = models.BooleanField()   # True indicates high frequency, False indicates low frequency
    visualized = models.BooleanField()       # True indicates visualized, False indicates numeric only
    
    # Funds available in the current round (carryover funds from the previous round plus investment returns)
    available_funds = models.CurrencyField()
    
    # Investment decision
    investment = models.CurrencyField(min=0, label="Investment amount")
    
    # Remaining funds (calculated automatically)
    remaining_funds = models.CurrencyField()
    
    # Stocks purchased in this round
    stocks_purchased = models.FloatField()
    
    # Whether the price is disclosed in this round (for record keeping)
    price_disclosed = models.BooleanField()


# Get the current session and round number within the session
def get_session_info(player):
    overall_round = player.round_number
    session_num = (overall_round - 1) // Constants.rounds_per_session + 1
    round_in_session = ((overall_round - 1) % Constants.rounds_per_session) + 1
    return session_num, round_in_session


# Retrieve the stock prices for the current session for the participant
def get_current_prices(player):
    session_num, _ = get_session_info(player)
    return player.participant.vars[f'stock_prices_{session_num}']


# Determine whether the price should be disclosed in this round
def is_price_disclosed(player, round_in_session):
    # High frequency group always shows the price
    if player.high_frequency:
        return True
    
    # For low frequency group: display the price in rounds 1, 2 and rounds based on the disclosure period
    if round_in_session <= 2:
        return True
    
    # For round 3 and onwards, determine based on the period
    # Apart from rounds 1 and 2, other rounds display according to the period
    # For example, when the period is 4, the displayed rounds are [1, 2, 6, 10, 14, 18]
    period = Constants.disclosure_period
    if round_in_session % period == 2:  # Rounds 2, 6, 10, 14, 18
        return True
    
    return False


# PAGES
class Introduction1(Page):
    @staticmethod
    def is_displayed(player):
        # Display the introduction page only in the first round
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        # Create a text display showing rounds 1, 2 and the periodic rounds
        period = Constants.disclosure_period
        disclosure_rounds = [1, 2]  # Always include rounds 1 and 2
        
        # Add periodic rounds (e.g., 2, 6, 10, 14, 18)
        for r in range(2, Constants.rounds_per_session + 1, period):
            if r > 2:  # Avoid adding round 2 again
                disclosure_rounds.append(r)
        
        # Create a user-friendly text display
        disclosure_rounds_text = ""
        for i, round_num in enumerate(disclosure_rounds):
            if i == 0:
                disclosure_rounds_text = str(round_num)
            elif i == len(disclosure_rounds) - 1:
                disclosure_rounds_text += " and " + str(round_num)
            else:
                disclosure_rounds_text += ", " + str(round_num)
        
        return {
            'high_frequency': player.high_frequency,
            'visualized': player.visualized,
            'disclosure_rounds': disclosure_rounds,
            'disclosure_rounds_text': disclosure_rounds_text,
            'num_sessions': Constants.num_sessions
        }
    
    @staticmethod
    def js_vars(player):
        return {
            'wait_time': 20  # 20 seconds wait time
        }


class RestPage(Page):
    @staticmethod
    def is_displayed(player):
        # Display after each session, except after the last session
        session_num, round_in_session = get_session_info(player)
        is_last_round_in_session = round_in_session == Constants.rounds_per_session
        return is_last_round_in_session and session_num < Constants.num_sessions
    
    @staticmethod
    def vars_for_template(player):
        session_num, _ = get_session_info(player)
        next_session = session_num + 1
        
        return {
            'current_session': session_num,
            'next_session': next_session,
            'total_sessions': Constants.num_sessions,
            'rest_time': Constants.rest_time
        }
    
    @staticmethod
    def js_vars(player):
        return {
            'wait_time': Constants.rest_time  # Rest time
        }


class Investment(Page):
    form_model = 'player'
    form_fields = ['investment']
    
    @staticmethod
    def vars_for_template(player):
        session_num, round_in_session = get_session_info(player)
        
        # Retrieve the stock prices for the current session
        stock_prices = get_current_prices(player)
        current_price = stock_prices[round_in_session - 1]
        
        # Determine whether the price should be disclosed in this round (using the new price disclosure rules)
        current_price_disclosed = is_price_disclosed(player, round_in_session)
        
        # Initialize variables for the previous round's information
        previous_remaining_funds = "0.00"
        previous_investment_value = "0.00"
        
        # Find the most recent round in which the price was disclosed
        last_disclosure_round = 1
        if not player.high_frequency and round_in_session > 1:
            # Check backwards from the current round to find the most recent disclosure round
            for r in range(round_in_session - 1, 0, -1):
                if is_price_disclosed(player, r):
                    last_disclosure_round = r
                    break
            
            player.participant.vars[f'last_disclosure_round_{session_num}'] = last_disclosure_round
        
        if round_in_session == 1:
            # For the first round of the session, use the initial endowment
            available_funds = float(Constants.initial_endowment)
        else:
            # Get the player object from the previous round
            previous_round = player.round_number - 1
            if previous_round >= 1:
                previous_player = player.in_round(previous_round)
                
                # If the price is not disclosed, use the decision from the most recent disclosure round
                if not current_price_disclosed and not player.high_frequency:
                    previous_remaining_funds = "{:.2f}".format(
                        player.participant.vars[f'last_disclosed_remaining_{session_num}'])
                    
                    # Retrieve the current price and the price at the most recent disclosure
                    last_disclosed_price = stock_prices[
                        player.participant.vars[f'last_disclosure_round_{session_num}'] - 1]
                    
                    # Calculate the change in investment value
                    value_change_ratio = current_price / last_disclosed_price if last_disclosed_price > 0 else 1
                    current_investment_value = player.participant.vars[f'last_disclosed_investment_{session_num}'] * value_change_ratio
                    previous_investment_value = "{:.2f}".format(current_investment_value)
                    
                    # Available funds remain unchanged (only show the previous round's remaining funds)
                    available_funds = float(player.participant.vars[f'last_disclosed_remaining_{session_num}'])
                else:
                    # Normal price disclosure situation
                    # Retrieve the previous round's remaining funds
                    previous_remaining_funds = "{:.2f}".format(float(previous_player.remaining_funds))
                    
                    # Calculate current funds: previous round's remaining funds + current investment value
                    previous_price = stock_prices[round_in_session - 2]
                    
                    # Calculate the current value of the previous round's investment
                    current_investment_value = float(previous_player.investment) * (current_price / previous_price)
                    previous_investment_value = "{:.2f}".format(current_investment_value)
                    
                    # Available funds = previous round's remaining funds + current investment value
                    available_funds = float(previous_player.remaining_funds) + current_investment_value
            else:
                # Fallback to initial endowment just in case
                available_funds = float(Constants.initial_endowment)
        
        # Save to the player object
        player.available_funds = cu(available_funds)
        
        # Create a price history for display
        price_history = []
        for r in range(1, round_in_session + 1):
            # Determine if this historical price should be disclosed
            price_disclosed = is_price_disclosed(player, r)
            
            if price_disclosed:
                price_display = f"${stock_prices[r - 1]}"
            else:
                price_display = "Not disclosed"
            
            # Include all rounds up to and including the current round
            price_history.append((r, price_display))
        
        # Prepare data for visualization
        prices = []
        rounds = []
        disclosed = []
        
        for r in range(1, round_in_session + 1):
            price = stock_prices[r - 1]
            is_disclosed_round = is_price_disclosed(player, r)
            
            # Only include disclosed prices
            if is_disclosed_round:
                prices.append(price)
                rounds.append(r)
                disclosed.append(True)
        
        # Format available funds as a string with two decimal places
        available_funds_str = "{:.2f}".format(available_funds)
        current_price_str = "{:.2f}".format(current_price)
        
        return {
            'current_price': current_price_str,
            'current_price_disclosed': current_price_disclosed,
            'price_history': price_history,
            'prices_json': json.dumps(prices),
            'rounds_json': json.dumps(rounds),
            'disclosed_json': json.dumps(disclosed),
            'available_funds': available_funds_str,
            'previous_remaining_funds': previous_remaining_funds,
            'previous_investment_value': previous_investment_value,
            'session_num': session_num,
            'round_in_session': round_in_session,
            'total_sessions': Constants.num_sessions,
        }
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        session_num, round_in_session = get_session_info(player)
        
        # Retrieve the stock prices for the current session
        stock_prices = get_current_prices(player)
        current_price = stock_prices[round_in_session - 1]
        
        # Determine whether the price is disclosed in this round (using the new price disclosure rules)
        current_price_disclosed = is_price_disclosed(player, round_in_session)
        
        player.price_disclosed = current_price_disclosed
        
        if current_price_disclosed:
            # When the price is disclosed, process the investment decision normally
            # Ensure the investment does not exceed available funds
            player.investment = min(player.investment, player.available_funds)
            
            # Calculate remaining funds
            player.remaining_funds = player.available_funds - player.investment
            
            # Calculate the stocks purchased (even if the price is unknown to the participant)
            if player.investment > 0:
                player.stocks_purchased = float(player.investment) / current_price
            else:
                player.stocks_purchased = 0
            
            # Save the decision made at this disclosure for use in future undisclosed rounds
            player.participant.vars[f'last_disclosed_investment_{session_num}'] = float(player.investment)
            player.participant.vars[f'last_disclosed_remaining_{session_num}'] = float(player.remaining_funds)
            player.participant.vars[f'last_disclosure_round_{session_num}'] = round_in_session
        else:
            # When the price is not disclosed, use the decision from the most recent disclosure round
            # Retrieve the price from the most recent disclosure round
            last_disclosed_round = player.participant.vars[f'last_disclosure_round_{session_num}']
            last_disclosed_price = stock_prices[last_disclosed_round - 1]
            
            # Calculate the current investment value (based on the current price)
            price_change_ratio = current_price / last_disclosed_price if last_disclosed_price > 0 else 1
            current_investment_value = player.participant.vars[f'last_disclosed_investment_{session_num}'] * price_change_ratio
            
            # In undisclosed rounds, the investment value is the current value of the stocks
            player.investment = cu(current_investment_value)
            
            # Remaining funds remain unchanged
            player.remaining_funds = cu(player.participant.vars[f'last_disclosed_remaining_{session_num}'])
            
            # Calculate the number of stocks currently held
            if last_disclosed_price > 0:
                player.stocks_purchased = player.participant.vars[f'last_disclosed_investment_{session_num}'] / last_disclosed_price
            else:
                player.stocks_purchased = 0


class Results(Page):
    @staticmethod
    def is_displayed(player):
        # Display at the last round of each session
        session_num, round_in_session = get_session_info(player)
        return round_in_session == Constants.rounds_per_session
    
    @staticmethod
    def vars_for_template(player):
        session_num, _ = get_session_info(player)
        
        # Retrieve the stock prices for the current session
        stock_prices = get_current_prices(player)
        
        # Calculate the first round of the current session
        first_round_of_session = player.round_number - Constants.rounds_per_session + 1
        
        # Retrieve the player objects for all rounds in the current session
        session_players = player.in_rounds(first_round_of_session, player.round_number)
        
        # Prepare the historical data
        history = []
        for p in session_players:
            round_offset = p.round_number - first_round_of_session
            price = stock_prices[round_offset]
            
            history.append({
                'round': round_offset + 1,
                'price': f"{price:.2f}",
                'disclosed': "Yes" if p.price_disclosed else "No",
                'available_funds': f"{p.available_funds:.2f}",
                'investment': f"{p.investment:.2f}",
                'remaining': f"{p.remaining_funds:.2f}",
                'stocks_purchased': f"{p.stocks_purchased:.4f}"
            })
        
        # Calculate the final result
        final_stock_price = stock_prices[Constants.rounds_per_session]  # Using the price after the 20th round of the current session
        final_stock_value = player.stocks_purchased * final_stock_price
        total_return = float(player.remaining_funds) + final_stock_value
        
        return {
            'history': history,
            'final_stock_price': f"{final_stock_price:.2f}",
            'final_stock_value': f"{final_stock_value:.2f}",
            'remaining_funds': f"{player.remaining_funds:.2f}",
            'stocks_purchased': f"{player.stocks_purchased:.4f}",
            'total_return': f"{total_return:.2f}",
            'session_num': session_num,
            'total_sessions': Constants.num_sessions,
        }


class FinalPage(Page):
    @staticmethod
    def is_displayed(player):
        # Display only in the final round of the experiment
        return player.round_number == Constants.num_rounds
    
    @staticmethod
    def vars_for_template(player):
        # Calculate the total earnings across all sessions
        total_earnings = 0
        session_results = []
        
        for session_num in range(1, Constants.num_sessions + 1):
            # Retrieve the last round of that session
            last_round_of_session = session_num * Constants.rounds_per_session
            if last_round_of_session <= player.round_number:
                session_player = player.in_round(last_round_of_session)
                
                # Retrieve the stock prices for that session
                stock_prices = player.participant.vars[f'stock_prices_{session_num}']
                
                # Calculate the final result
                final_stock_price = stock_prices[Constants.rounds_per_session]  # Using the price after the 20th round of that session
                final_stock_value = session_player.stocks_purchased * final_stock_price
                session_return = float(session_player.remaining_funds) + final_stock_value
                
                total_earnings += session_return
                
                session_results.append({
                    'session_num': session_num,
                    'total_return': f"{session_return:.2f}"
                })
        
        return {
            'session_results': session_results,
            'average_earnings': f"{total_earnings/4:.2f}"
        }


# Page sequence
page_sequence = [Introduction1, Investment, Results, RestPage, FinalPage]
