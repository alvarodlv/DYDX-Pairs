import logging
import time

from decouple import config
from datetime import datetime, timedelta
from dydx3 import Client
from web3 import Web3
from funcs import initiate_logger
from constants import (
    HOST,
    ETHEREUM_ADDRESS,
    DYDX_API_KEY,
    DYDX_API_SECRET,
    DYDX_PASSPHRASE,
    STARK_PRIVATE_KEY,
    HTTP_PROVIDER
)


class DYDX():

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, filename='logging/api_log.log', format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')
        self.logger = initiate_logger('logging/api_log.log')

        return

    def connect_dydx(self):

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
                market = position['Market']

                # Determine side
                side = 'BUY'
                if position['side'] == 'LONG':
                    side = 'SELL'
            

        return 
