from dydx import DYDX
from funcs import send_message
from constants import ABORT_ALL_POSITIONS, FIND_CONIT_PARIS, PLACE_TRADES, MANAGE_EXITS
from entry import open_position
from exits import manage_trade_exits
from cointegrated_pairs import (
    store_coint_results)


if __name__ == '__main__':
    
    # Connect DYDX
    dYdX = DYDX()

    # Log In
    client = dYdX.connect_dydx()
    send_message('Successfully conected to dYdX client.')

    # Abort all open positions
    if ABORT_ALL_POSITIONS:
        close_orders = dYdX.abort_all_positions(client)
        send_message('Aborted all open positions.')

    # Find cointegrated pairs
    if FIND_CONIT_PARIS:
        df_market_prices = dYdX.construct_market_prices(client)
        stored_results = store_coint_results(df_market_prices)
        send_message('Downloaded market prices and stored conitegrated pairs.')

    # Run as always on
    while True:

        # Place trades for opening positions
        if MANAGE_EXITS:
            manage_trade_exits(client) 
            send_message('Managed existing trades successfully.')

        # Place trades for opening positions
        if PLACE_TRADES:
            open_position(client)
            send_message('Opened positions successfully.')