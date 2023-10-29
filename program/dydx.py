import logging
import time
import numpy as np
import pandas as pd

from decouple import config
from pprint import pprint
from datetime import datetime, timedelta
from dydx3 import Client
from web3 import Web3
from funcs import initiate_logger, format_price, get_iso
from constants import (
    HOST,
    ETHEREUM_ADDRESS,
    DYDX_API_KEY,
    DYDX_API_SECRET,
    DYDX_PASSPHRASE,
    STARK_PRIVATE_KEY,
    HTTP_PROVIDER,
    RESOLUTION
)


class DYDX():

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, filename='logging/api_log.log', format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')
        self.logger = initiate_logger('logging/api_log.log')

        return

    def connect_dydx(self):

        '''
        Establish connection to dYdX platform.
        :return: dYdX client
        '''

        # Log
        self.logger.info(f'[START] Initiating connection to dydX.')

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

            self.logger.info(f'[COMPLETE] Connection to dYdX established.')

        except:
            self.logger.exception(f'[ERROR] Failed to establish connection to dYdX.')
            exit(1)

        return client
    
    def account_info(self, client):

        '''
        Retrieve account informatiion.

        :param client: dYdX client
        :return account: dict containing account information
        '''

        # Log
        self.logger.info(f'[START] Retrieving account information.')

        # Retrieve account info
        try:
            account = client.private.get_account()
            self.logger.info(f'[COMPLETE] Account information retrieved.')

        except:
            self.logger.exception(f'[ERROR] Failed to retrieve account information.')
            exit(1)

        return account
    
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
        self.logger.info(f'[START] Placing market order for {market} at quantity {size}.')


        # Get Position ID
        try:
            account = self.account_info(client)
            position_id = account.data['account']['positionId']
            self.logger.info(f'[COMPLETE] Retrieved acocunt position ID.')
        
        except:
            self.logger.exception(f'[ERROR] Failed to retrieve account position ID.')
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
            self.logger.info(f'[COMPLETE] Retrieved acocunt position ID.')

        except:
            self.logger.exception(f'[ERROR] Failed to place order.')
            exit(1)

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
        self.logger.info(f'[START] Aborting all open positions.')

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
                accept_price = format_price(accept_price, tick_size)

                # Place order to close
                order = self.place_market_order(client, market, side, position['sumOpen'], accept_price, True)
                close_orders.append(order)
                time.sleep(.05)
            
        return close_orders
    
    def construct_market_prices(self, client):

        '''
        Construct dataframe of market prices.

        :param client: dYdX client
        :return : dataframe 
        '''

        # Log
        self.logger.info(f'[START] Constructing market prices.')

        # Get time periods
        ISO_TIMES = get_iso()

        pprint(ISO_TIMES)

        return
