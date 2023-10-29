from dydx import DYDX
from constants import ABORT_ALL_POSITIONS, FIND_CONIT_PARIS
from pprint import pprint

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

    # 

