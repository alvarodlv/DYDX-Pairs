import json
import pandas as pd
import numpy as np

from funcs import format_number, initiate_logger, send_message
from constants import ZSCORE_THRESH, USD_PER_TRADE, USD_MIN_COLLATERAL
from cointegrated_pairs import calc_z_score
from dydx import DYDX
from orderBot import BotAgent

def open_position(client):

    # Initialise logger
    logger = initiate_logger('logging/api_log.log')

    # Read in coint pairs
    df = pd.read_csv('coint_pairs.csv')

    # Get markets
    markets = client.public.get_markets().data

    # Initialise container for BotAgent results
    bot_agents = []

    # Open open trade json file
    try:
        with open('bot_agents.json') as f:
            open_positions_file = json.load(f)
        
        for p in open_positions_file:
            bot_agents.append(p)
    except:
        bot_agents = []

    # Log & initialise illiquid pairs list
    logger.info(f'[OPEN_POSITION] - [START] Beginning process of opening orders.')
    illiquid_pairs = []

    # Find z-score trigger
    for index, row in df.iterrows():

        # Vars
        base_market = row['base_market']
        quote_market = row['quote_market']
        hedge_ratio = row['hedge_ratio']
        half_life = row['half_life']
    
        # Get prices
        series_1 = DYDX().get_recent_candles(client, base_market)
        series_2 = DYDX().get_recent_candles(client, quote_market)

        # Get z-score
        if len(series_1) > 0 and len(series_1) == len(series_2) and base_market not in illiquid_pairs and quote_market not in illiquid_pairs:
            spread = series_1 - (hedge_ratio*series_2)
            z_score = calc_z_score(spread).values.tolist()[-1]

            # Establish if potential trade
            if abs(z_score) >= ZSCORE_THRESH:

                # Ensure not already open
                is_base_open = DYDX().is_open_positions(client, base_market)
                is_quote_open = DYDX().is_open_positions(client, quote_market)

                # Place Trade
                if not is_base_open and not is_quote_open:

                    # Determine trade
                    base_side = 'BUY' if z_score < 0 else 'SELL'
                    quote_side = 'BUY' if z_score > 0 else 'SELL'

                    # Get acceptable price in str format with correct dec
                    base_price = series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99
                    accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99
                    failsafe_base_price = float(base_price) * 0.05 if z_score < 0 else float(base_price) * 1.7
                    base_tick_size = markets['markets'][base_market]['tickSize']
                    quote_tick_size = markets['markets'][quote_market]['tickSize']

                    # Format prices
                    accept_base_price = format_number(accept_base_price, base_tick_size)
                    accept_quote_price = format_number(accept_quote_price, quote_tick_size)
                    accept_failsafe_base_price = format_number(failsafe_base_price, base_tick_size)

                    '''
                    CAN ADD KELLY CRITERION HERE
                    '''

                    # Get size
                    base_quantity = 1 / base_price * USD_PER_TRADE
                    quote_quantity = 1 / quote_price * USD_PER_TRADE
                    base_step_size = markets['markets'][base_market]['stepSize']
                    quote_step_size = markets['markets'][quote_market]['stepSize']

                    # Format sizes
                    base_size = format_number(base_quantity, base_step_size)
                    quote_size = format_number(quote_quantity, quote_step_size)

                    # # Format sizes
                    # base_size = format_number(format_step(base_quantity, base_step_size),base_step_size)
                    # quote_size = format_number(format_step(quote_quantity, quote_step_size),quote_step_size)

                    # Ensure size
                    base_min_order_size = markets['markets'][base_market]['minOrderSize']
                    quote_min_order_size = markets['markets'][quote_market]['minOrderSize']
                    check_base = float(base_quantity) > float(base_min_order_size)
                    check_quote = float(quote_quantity) > float(quote_min_order_size)

                    # # if checks pass, place trade
                    if not check_base and not check_quote:
                        continue

                    # Check account balance
                    #_, free_collateral = DYDX().account_info(client)
                    account = client.private.get_account()
                    free_collateral = float(account.data['account']['freeCollateral'])

                    # Guard: Ensure collateral
                    if free_collateral < USD_MIN_COLLATERAL:
                        break

                    # Create Bot Agent
                    logger.info(f'[OPEN_POSITION] - [START] Processing orders for {base_market} & {quote_market}.')
                    bot_agent = BotAgent(
                            client,
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=accept_failsafe_base_price,
                            z_score=z_score,
                            half_life=half_life,
                            hedge_ratio=hedge_ratio
                        )
                    
                    # Open trades
                    bot_open_dict, illiquid = bot_agent.open_trades()
                    if illiquid not in illiquid_pairs:
                        illiquid_pairs = illiquid_pairs + illiquid

                    # Handle success in opening trades
                    if bot_open_dict['pair_status'] == 'LIVE':

                        # Append to list of bot agents
                        bot_agents.append(bot_open_dict)
                        message = f'Opened following pairs position: {base_market} and {quote_market}. Current account free collateral sits at: {free_collateral}'
                        send_message(message)
                        del bot_open_dict

    # Save agents
    if len(bot_agents) > 0:
        logger.info(f'[OPEN_POSITION] - [COMPLETE] Open positions completed.')
        with open('bot_agents.json','w') as f:
            json.dump(bot_agents, f, indent=4)
    
    else:
        logger.exception(f'[OPEN_POSITION] - [COMPLETE] Did not open any positions.')
                        

    return
