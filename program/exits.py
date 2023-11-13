import json
import time
import pandas as pd

from funcs import format_number, initiate_logger, send_message
from constants import CLOSE_AT_ZSCORE_CROSS, DIR
from cointegrated_pairs import calc_z_score
from dydx import DYDX
from pprint import pprint

def manage_trade_exits(client):
    '''
    Manage exiting open positions based on criteria
    set in constants.
    '''

    # Initiate logger
    logger = initiate_logger()
    tele_message = '💸 ----- MANAGE TRADES ----- 💸\n\nClosed the following positions:\n'
    exit_pos = 0

    # Initialise saving output
    save_output = []

    # Open coint_pairs.csv
    df_coint = pd.read_csv(DIR+'/coint_pairs.csv')

    # Open trade json file
    try:
        with open(DIR+'/bot_agents.json') as f:
            open_positions_file = json.load(f)
    except:
        return 'complete', exit_pos
    
    # Guard exit if no open positions
    if len(open_positions_file) < 1:
        return 'complete', exit_pos
    
    # Get all open positions per trading platform
    logger.info('[MANAGE_EXIT] - Managing exits of current trades.')
    exchange_pos = client.private.get_positions(status='OPEN')
    all_exc_pos = exchange_pos.data['positions']
    markets_live = []
    for p in all_exc_pos:
        markets_live.append(p['market'])

    # Check all saved positions match order record
    # Exit trade according to any exit trade rules
    for position in open_positions_file:

        # Initialise is_close trigger
        is_close = False

        # Extract position matching info from file - market 1
        position_market_m1 = position['market_1']
        position_size_m1 = position['order_m1_size']
        position_side_m1 = position['order_m1_side']

        # Extract position matching info from file - market 2
        position_market_m2 = position['market_2']
        position_size_m2 = position['order_m2_size']
        position_side_m2 = position['order_m2_side']

        # Protect API
        time.sleep(0.5)

        # Get order info m1 per exchange
        order_m1 = client.private.get_order_by_id(position['order_id_m1'])
        order_market_m1 = order_m1.data['order']['market']
        order_size_m1 = order_m1.data['order']['size']
        order_side_m1 = order_m1.data['order']['side']

        # Get order info m2 per exchange
        order_m2 = client.private.get_order_by_id(position['order_id_m2'])
        order_market_m2 = order_m2.data['order']['market']
        order_size_m2 = order_m2.data['order']['size']
        order_side_m2 = order_m2.data['order']['side']

        # Matching checks 
        check_m1 = position_market_m1 == order_market_m1 and position_size_m1 == order_size_m1 and position_side_m1 == order_side_m1
        check_m2 = position_market_m2 == order_market_m2 and position_size_m2 == order_size_m2 and position_side_m2 == order_side_m2
        check_live = position_market_m1 in markets_live and position_market_m2 in markets_live

        # Guard if all not True
        if not check_m1 or not check_m2 or not check_live:
            logger.info(f'[MANAGE_EXIT] - Not all open positions match exchange records for {position_market_m1} and {position_market_m2}.')
            continue

        # Get prices
        series_1 = DYDX().get_recent_candles(client=client, market=position_market_m1)
        time.sleep(0.1)
        series_2 = DYDX().get_recent_candles(client=client, market=position_market_m2)
        time.sleep(0.1)

        # Get markets for reference of tickSize
        markets = client.public.get_markets().data
        time.sleep(0.1)

        # Trigger close based on z-score
        if CLOSE_AT_ZSCORE_CROSS:

            # Initialise z-scores
            hedge_ratio = position['hedge_ratio']
            z_score_traded = position['z_score']
            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - (hedge_ratio*series_2)
                z_score_current = calc_z_score(spread).values.tolist()[-1]

            # Determine trigger
            z_score_level_check = abs(z_score_current >= abs(z_score_traded))
            z_score_cross_check = (z_score_current < 0 and z_score_traded > 0) or (z_score_current > 0 and z_score_traded < 0)

            # Set trigger for not coint pairs 
            pairs_1 = list(df_coint['base_market']+' '+df_coint['quote_market'])
            pairs_2 = list(df_coint['quote_market']+' '+df_coint['base_market'])
            pair = position_market_m1 +' ' + position_market_m2
            coint_check = pair in pairs_1 or pair in pairs_2
            if coint_check == False:
                logger.info(f'[MANAGE_EXIT] - {pair} no longer cointegrated. Attempt to close.')

            # Close trade
            if (z_score_level_check and z_score_cross_check) or coint_check == False:

                # Initiate close trigger
                is_close = True

        '''
        ANY OTHER CLOSING LOGIC
        '''
        
        # Close position if triggered
        if is_close:

            # Determine side - m1
            side_m1 = 'SELL'
            if position_side_m1 == 'SELL':
                side_m1 = 'BUY'

            # Determine side - m2
            side_m2 = 'SELL'
            if position_side_m2 == 'SELL':
                side_m2 = 'BUY'

            # Get and format price
            price_m1 = float(series_1[-1])
            price_m2 = float(series_2[-1])
            accept_price_m1 = price_m1 * 1.05 if side_m1 == 'BUY' else price_m1 * 0.95
            accept_price_m2 = price_m2 * 1.05 if side_m2 == 'BUY' else price_m2 * 0.95
            tick_size_m1 = markets['markets'][position_market_m1]['tickSize']
            tick_size_m2 = markets['markets'][position_market_m2]['tickSize']
            accept_price_m1 = format_number(accept_price_m1, tick_size_m1)
            accept_price_m2 = format_number(accept_price_m2, tick_size_m2)

            # Close positions
            try:

                # Close position for market 1
                close_order_1 = DYDX().place_market_order(
                    client,
                    market=position_market_m1,
                    side=side_m1,
                    size=position_size_m1,
                    price=accept_price_m1,
                    reduce_only=True
                )

                time.sleep(1)

                # Close position for market 2
                close_order_2 = DYDX().place_market_order(
                    client,
                    market=position_market_m2,
                    side=side_m2,
                    size=position_size_m2,
                    price=accept_price_m2,
                    reduce_only=True
                )

                time.sleep(1)
                exit_pos +=1
                if coint_check:
                    tele_message += f'{position_market_m1} %26 {position_market_m2}: crossed.\n'
                else:
                    tele_message += f'{position_market_m1} %26 {position_market_m2}: not coint.\n'

            except:
                save_output.append(position)
                logger.exception(f'[MANAGE_EXIT] - Exit failed for {position_market_m1} & {position_market_m2}.')

        # Keep record of items and save
        else:
            save_output.append(position)

    # Save remaining items
    with open(DIR+'/bot_agents.json','w') as f:
        json.dump(save_output, f, indent=4)

    if exit_pos == 0:
        tele_message = ''

    logger.info(f'[MANAGE_EXIT] - {len(save_output)} positions remaining.')

    return tele_message, exit_pos
