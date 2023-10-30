from dydx import DYDX
from pprint import pprint
from constants import ABORT_ALL_POSITIONS, FIND_CONIT_PARIS, PLACE_TRADES
from entry import open_position
from cointegrated_pairs import (
    calc_half_life, 
    calc_z_score, 
    calc_coint, 
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

    # Place trades for opening positions
    if PLACE_TRADES:
        open_position(client)