import time
import json
import numpy as np
import pandas as pd

from decouple import config
from timeit import default_timer as timer
from pprint import pprint
from datetime import datetime, timedelta
from dydx3 import Client
from web3 import Web3
from funcs import format_number, get_iso, initiate_logger
from cointegrated_pairs import calc_z_score
from constants import (
    HOST,
    ETHEREUM_ADDRESS,
    DYDX_API_KEY,
    DYDX_API_SECRET,
    DYDX_PASSPHRASE,
    STARK_PRIVATE_KEY,
    HTTP_PROVIDER,
    RESOLUTION,
    DIR
)


class DYDX():

    def __init__(self):
        self.logger = initiate_logger()
        return

    def connect_dydx(self):
        '''
        Establish connection to dYdX platform.
        :return: dYdX client
        '''

        # Log
        self.logger.info(f'[CONNECTION] - Initiating connection to dydX.')

        # Initiate Connection
        try:
            client = Client(
            host=HOST,
            api_key_credentials={
                'key': DYDX_API_KEY,
                'secret': DYDX_API_SECRET,
                'passphrase': DYDX_PASSPHRASE
            },
            stark_private_key=STARK_PRIVATE_KEY,
            eth_private_key=config('ETH_PRIVATE_KEY'),
            default_ethereum_address=ETHEREUM_ADDRESS,
            web3=Web3(Web3.HTTPProvider(HTTP_PROVIDER))
            )

            self.logger.info(f'[CONNECTION] - Connection to dYdX established.')

        except:
            self.logger.exception(f'[CONNECTION] - Failed to establish connection to dYdX.')
            exit(1)

        return client
    
    def account_info(self, client):
        '''
        Retrieve account informatiion.

        :param client: dYdX client
        :return account: dict containing account information
        '''

        # Retrieve account info
        try:
            account = client.private.get_account()
            free_collateral = account.data['account']['freeCollateral']

        except:
            self.logger.exception(f'[ACCOUNT_INFO] - Failed to retrieve account information.')
            exit(1)

        return account, float(free_collateral)
    
    def place_market_order(self, client, market, side, size, price, reduce_only):
        '''
        Place market order.

        :param client: dYdX client
        :param market: crypto pair
        :param side: 'BUY' or 'SELL'
        :param size: quantity of order
        :param price: max/min price of order. If buy, higher; if sell, lower
        :reduce_only: if True, will net with current positions
        :return placed_order.data: dict of order results
        '''

        # Log
        self.logger.info(f'[MARKET_ORDER] - Placing market order for. Market: {market}; Side: {side}; Size: {size}; Price: {price}.')


        # Get Position ID
        try:
            account, _ = self.account_info(client)
            position_id = account.data['account']['positionId']
        
        except:
            self.logger.exception(f'[MARKET_ORDER] - Failed to retrieve account position ID.')
            exit(1)

        # Get Expiration Time
        server_time = client.public.get_time()
        expiration = datetime.fromisoformat(server_time.data['iso'].replace('Z','+00:00')) + timedelta(seconds=90)

        # Place Order
        try:
            placed_order = client.private.create_order(
                position_id=position_id, 
                market=market,
                side=side,
                order_type='MARKET',
                post_only=False,
                size=size,
                price=price, # If BUY - higher than price, if SELL - lower than price
                limit_fee='0.015',
                expiration_epoch_seconds=expiration.timestamp(),
                time_in_force='FOK', # Fill or Kill
                reduce_only=reduce_only # If True - will net with previous orders
                )
            self.logger.info(f'[MARKET_ORDER] - Placed order for {market}.')

        except:
            self.logger.exception(f'[MARKET_ORDER] - Failed to place order for {market}.')

        return placed_order.data
    
    def abort_all_positions(self, client):
        '''
        Aborts all positions. 
        1. Find tickSize for all pairs
        2. Get all positons in account
        3. Handle open positions
        4. Places inverse positions to orders in account

        :param client: dYdX client
        :return close_orders: list of dicts for all inverse positions
        '''

        # Log
        self.logger.info(f'[ABORT_TRADE] - Aborting all open positions.')

        # Cancel all orders
        client.private.cancel_all_orders()
        time.sleep(0.5)

        # Get markets for reference of tick size
        markets = client.public.get_markets().data
        time.sleep(0.5)

        # Get all open positions
        positions = client.private.get_positions(status='OPEN')
        all_positions = positions.data['positions']

        # Handle open positions
        close_orders = []
        if len(all_positions) > 0:
            for position in all_positions:

                # Determine market
                market = position['market']

                # Determine side
                side = 'BUY'
                if position['side'] == 'LONG':
                    side = 'SELL'

                # Get Price
                price = float(position['entryPrice'])
                accept_price = price * 1.25 if side == 'BUY' else price * 0.75
                tick_size = markets['markets'][market]['tickSize']
                accept_price = format_number(accept_price, tick_size)

                # Place order to close
                try:
                    order = self.place_market_order(client, market, side, position['sumOpen'], accept_price, True)
                    close_orders.append(order)
                    time.sleep(.2)

                    # Ensure order is filled
                    order_status = self.check_order_status(client, order['order']['id'])
                    time.sleep(0.5)

                    # Abort if order unfilled
                    if order_status == 'CANCELED':
                        self.logger.exception(f'[ABORT_TRADE] - Market {market} failed to abort.')

                    self.logger.info(f'[ABORT_TRADE] - {market} successfully aborted.')
                
                except:
                    self.logger.exception(f'[ABORT_TRADE] - Market {market} failed to abort.')

            # Clear bot agents file
            bot_agents = []
            with open(DIR+'/bot_agents.json','w') as f:
                      json.dump(bot_agents, f)
        else:
            self.logger.info('[ABORT_TRADE] - No positions to abort. Empty portfolio.')
            
        return close_orders
    
    def get_hist_candles(self, client, market):
        '''
        Get historical candles 

        :param client: dYdX client
        :param market: Market pair
        :return close_prices: dict if close prices for market pair
        '''

        # Define output
        close_prices = []

        # Extract historical price data for each timeframe
        ISO_TIMES = get_iso()
        for timeframe in reversed(ISO_TIMES.keys()):

            # Confirm times needewd
            tf_obj = ISO_TIMES[timeframe]
            from_iso = tf_obj['from_iso']
            to_iso = tf_obj['to_iso']

            # Get data
            try:
                candles = client.public.get_candles(
                    market=market,
                    resolution=RESOLUTION,
                    from_iso=from_iso,
                    to_iso=to_iso,
                    limit=100
                )
            except:
                self.logger.exception(f'[GET_HIST] - Unable to source historical candles for market pair: {market}')

            # Structure data
            for candle in candles.data['candles']:
                close_prices.append({'datetime': candle['startedAt'], market: candle['close']})

            # Construct dict
            close_prices.reverse()
        

        # Log
        self.logger.info(f'[GET_HIST] - Close prices for market pair {market} saved.')

        return close_prices

    
    def construct_market_prices(self, client):
        '''
        Construct dataframe of market prices.

        :param client: dYdX client
        :return df: dataframe containing close prices
        '''

        # Log
        self.logger.info(f'[MARKET_PRICES] - Constructing market prices.')
        start = timer()

        # Define variables
        tradeable_markets = []
        markets = client.public.get_markets()

        # Find tradeable pairs
        for market in markets.data['markets'].keys():
            market_info = markets.data['markets'][market]
            if market_info['status'] == 'ONLINE' and market_info['type'] == 'PERPETUAL':
                tradeable_markets.append(market)

        # Set initial dataframe
        close_prices = self.get_hist_candles(client, tradeable_markets[0])
        df = pd.DataFrame(close_prices)
        df.set_index('datetime', inplace=True)

        # Append other prices to df
        for market in tradeable_markets[1:]:
            close_prices_add = self.get_hist_candles(client, market)
            df_add = pd.DataFrame(close_prices_add)
            df_add.set_index('datetime', inplace=True)
            df = pd.merge(df, df_add, how='outer', on='datetime', copy=False)
            del df_add
        
        # Sort by datewtime index
        df = df.sort_index()

        # Bfill nans
        df = df.bfill()
        
        # Check any cols with Nan
        nans = df.columns[df.isna().any()].tolist()
        if len(nans) > 0:
            self.logger.info(f'[MARKET_PRICES] - Dropping following market pairs with Nans: {nans}.')
            df.drop(columns=nans, inplace=True)
        
        end = timer()
        self.logger.info(f'[MARKET_PRICES] - Market prices stored in dataframe. {round((end-start)/60,2)} mins')

        return df
    
    def check_order_status(self, client, orderId):
        '''
        Check status of specific order. 

        :param client: dYdX client
        :param orderId: Order identifier.
        :return status: Status of order queried
        '''

        # Get order by id
        order = client.private.get_order_by_id(orderId)

        if order.data:
            if 'order' in order.data.keys():
                return order.data['order']['status']
        
        self.logger.info(f'[CHECK_ORDER_STATUS] - Unable to check status of order: {orderId}')
        
        return 'FAILED'
    
    def get_recent_candles(self, client, market):
        '''
        Retrieve recent candle for market pair 

        :param client: dYdX client
        :param market: Market pair
        :return prices_result: Array of prices
        '''

        # Initialise array
        close_prices = []
        time.sleep(0.2)

        # Get candles
        try:
            candles = client.public.get_candles(
                market=market,
                resolution=RESOLUTION,
                limit=100
            )

        except:
            self.logger.exception(f'[GET_RECENT] - Unable to source recent candles for market pair: {market}')

        # Structure data
        for candle in candles.data['candles']:
            close_prices.append(candle['close'])

        # Construct and return close price series
        close_prices.reverse()
        prices_result = np.array(close_prices).astype(float)

        return prices_result

    def is_open_positions(self, client, market):
        '''
        Check if there are any open position for prospective trade.

        :param client: dYdX client
        :param market: Market pair
        :return boolean: True or False if exists
        '''

        time.sleep(0.2)

        # Get positions
        all_positions = client.private.get_positions(
            market=market,
            status='OPEN',
        )

        # Determine if open
        if len(all_positions.data['positions']) > 0:
            return True
        else:
            return False