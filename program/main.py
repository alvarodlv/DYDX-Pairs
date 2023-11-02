from dydx import DYDX
from pprint import pprint
from funcs import initiate_logger
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

    # Abort all open positions
    if ABORT_ALL_POSITIONS:
        close_orders = dYdX.abort_all_positions(client)

    # Find cointegrated pairs
    if FIND_CONIT_PARIS:
        df_market_prices = dYdX.construct_market_prices(client)
        stored_results = store_coint_results(df_market_prices)

    # Run as always on
    while True:

        # Place trades for opening positions
        if MANAGE_EXITS:
            manage_trade_exits(client) 

        # Place trades for opening positions
        if PLACE_TRADES:
            open_position(client)