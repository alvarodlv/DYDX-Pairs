import time

from dydx import DYDX
from funcs import send_message
from constants import ABORT_ALL_POSITIONS, FIND_CONIT_PARIS, PLACE_TRADES, MANAGE_EXITS, PERIOD_OF_TIME, START_BALANCE
from entry import open_position
from exits import manage_trade_exits
from cointegrated_pairs import (
    store_coint_results)


if __name__ == '__main__':
    
    # Connect DYDX
    dYdX = DYDX()

    # Log In
    client = dYdX.connect_dydx()
    send_message(f'⚡ DYDX Pairs Trading Bot Initiated ⚡\n_________________________________\n\nSuccessfully conected to dYdX client.\n\nBot Parameters...\nAbort all positions: {ABORT_ALL_POSITIONS}\nFind cointegrated pairs: {FIND_CONIT_PARIS}\nManage existing trades: {MANAGE_EXITS}\nPlace new trades: {PLACE_TRADES}\n')

    # Abort all open positions
    tele_message = '----- DATA %26 OPEN POSITIONS -----\n\n'
    if ABORT_ALL_POSITIONS:
        close_orders = dYdX.abort_all_positions(client)
        if len(close_orders) > 0:
            tele_message += 'Aborted all open positions.\n'
        else: 
            tele_message += 'No positions to abort.\n'
    else:
        tele_message += 'Decided not to abort any positions.\n'

    # Find cointegrated pairs
    if FIND_CONIT_PARIS:
        df_market_prices = dYdX.construct_market_prices(client)
        stored_results = store_coint_results(df_market_prices)
        tele_message += 'Downloaded market prices and stored conitegrated pairs.\n'
    else:
        tele_message += 'Not downloading new market data.\n'
    
    # Update telegram
    send_message(tele_message)


    # Place trades for opening positions
    if MANAGE_EXITS:
        tele_message, exit_pos = manage_trade_exits(client)
        if len(tele_message) > 1 and tele_message != 'complete':
            send_message(tele_message)

    # Place trades for opening positions
    if PLACE_TRADES:
        tele_message, new_pos = open_position(client)
        if len(tele_message) > 1:
            send_message(tele_message)

    # Stats
    account = client.private.get_account()
    raw_collat = float(account.data['account']['equity'])
    free_collateral = '${:,.2f}'.format(raw_collat)
    raw_equity = float(account.data['account']['equity'])
    equity = '${:,.2f}'.format(raw_equity)
    raw_percent = (raw_equity / START_BALANCE - 1)*100
    returns = '{:.2f}'.format(raw_percent)
    send_message(f'----- STATS -----\n\nAccount equity: {equity}\nFree Collateral: {free_collateral}\nCurrent return: {returns}%\nOpened positions: {new_pos}\nManaged positions: {exit_pos}')

    # Complete message
    send_message('Bot complete. Have a great day.')