import time
import logging

from dydx import DYDX
from datetime import datetime, timedelta
from funcs import initiate_logger
from pprint import pprint

class BotAgent():
    '''
    Class to cover managing and chekcing trades
    '''

    def __init__(self, 
                 client,
                 market_1, 
                 market_2, 
                 base_side,
                 base_size, 
                 base_price, 
                 quote_side,
                 quote_size, 
                 quote_price, 
                 accept_failsafe_base_price,
                 z_score,
                 half_life,
                 hedge_ratio
                 ):
        
        # Set logger
        self.logger = logging.getLogger('logging/api_log.log')

        # Initialise class vars
        self.illiquid = []
        self.client = client
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio

        # Initialise output vars
        self.order_dict = {
            'market_1': market_1,
            'market_2': market_2,
            'hedge_ratio': hedge_ratio,
            'z_score': z_score,
            'half_life': half_life,
            'order_id_m1': '',
            'order_m1_size': base_size,
            'order_m1_side': base_side,
            'order_time_m1': '',
            'order_id_m2': '',
            'order_m2_size': quote_size,
            'order_m2_side': quote_side,
            'order_time_m2': '',
            'pair_status': '',
            'comments': ''
        }

    def check_order_status_by_id(self, order_id):

        # Check order status
        order_status = DYDX().check_order_status(client=self.client, orderId=order_id)

        # Guard: If order canclled, move to next pair
        if order_status == 'CANCELED':
            self.logger.info(f'[CHECK_STATUS] - Order cancelled.')
            self.order_dict['pair_status'] == 'FAILED'

            return 'failed'
        
        # Guard: If order not filled, wait until order expiration
        if order_status != 'FAILED':
            time.sleep(2)
            order_status = DYDX().check_order_status(client=self.client, orderId=order_id)

            # Check if cancelled again
            if order_status == 'CANCELED':
                self.logger.info(f'[CHECK_STATUS] - Order ERROR: {order_id}')
                self.order_dict['pair_status'] == 'FAILED'

                return 'failed'
            
            # Guard: If not filled, cancel order
            if order_status != 'FILLED':
                self.client.private.cancel_order(order_id=order_id)
                self.order_dict['pair_status'] == 'ERROR'
                self.logger.info(f'[CHECK_STATUS] - Order ERROR: {order_id}')

                return 'error'
            
        self.logger.info(f'[CHECK_STATUS] - Order SUCCESS: {order_id}')
            
        return 'live'
                
    def open_trades(self):

        # Log
        self.logger.info(f'[OPEN_TRADE] - Starting order process.')
        self.logger.info(f'[OPEN_TRADE] - Placing order for base pair: {self.market_1}.')

        # Place base order
        try:                                   
            base_order = DYDX().place_market_order(self.client, self.market_1, self.base_side, self.base_size, self.base_price, False)

            # Store order ID
            self.order_dict['order_id_m1'] = base_order['order']['id']
            self.order_dict['order_time_m1'] = datetime.now().isoformat()

        except Exception as e:
            self.order_dict['pair_status'] = 'ERROR'
            self.order_dict['comments'] = f'Market 1 {self.market_1}: {e}'
            self.logger.info(f'[OPEN_TRADE] - Market 1 {self.market_1}: {e}')
            self.illiquid.append(self.market_1)
            return self.order_dict, self.illiquid
        
        # Ensure order is live before processing
        order_status_m1 = self.check_order_status_by_id(self.order_dict['order_id_m1'])

        # Abort if order unfilled
        if order_status_m1 != 'live':
            self.order_dict['pair_status'] = 'ERROR'
            self.order_dict['comments'] = f'Market 1 {self.market_1} failed to fill.'
            self.illiquid.append(self.market_1)
            return self.order_dict, self.illiquid
        
        # Log
        self.logger.info(f'[OPEN_TRADE] - Placing order for quote pair: {self.market_2}.')

        # Place quote order
        try:
            quote_order = DYDX().place_market_order(self.client, self.market_2, self.quote_side, self.quote_size, self.quote_price, False)

            # Store order ID
            self.order_dict['order_id_m2'] = quote_order['order']['id']
            self.order_dict['order_time_m2'] = datetime.now().isoformat()

        except Exception as e:
            self.order_dict['pair_status'] = 'ERROR'
            self.order_dict['comments'] = f'Market 2 {self.market_2}: {e}'
            self.logger.info(f'[OPEN_TRADE] - Market 2 {self.market_2}: {e}')
            self.illiquid.append(self.market_2)
            return self.order_dict, self.illiquid
        
        # Ensure order is live before processing
        order_status_m2 = self.check_order_status_by_id(self.order_dict['order_id_m2'])

        # Abort if order filled
        if order_status_m2 != 'live':
            self.order_dict['pair_status'] = 'ERROR'
            self.illiquid.append(self.market_2)
            self.order_dict['comments'] = f'Market 2 {self.market_2} failed to fill.'
        
            # Close order 1
            try:
                close_order = DYDX().place_market_order(self.client, self.market_1, self.quote_side, self.base_size, self.accept_failsafe_base_price, True)

                # Ensure order is live before proceeding
                time.sleep(5)
                order_status_close_order = DYDX().check_order_status(client=self.client, orderId=close_order['order']['id'])
                if order_status_close_order != 'FILLED':
                    self.log.exception(f'[OPEN_TRADE] - Abort program. Unable to close base position with fail safe.')
                    exit(1)

            except Exception as e:
                self.order_dict['pair_status'] = 'ERROR'
                self.order_dict['comments'] = f'Close Market 2 {self.market_2}: {e}'
                self.logger.info(f'[OPEN_TRADE] - Error closing Market 1 {self.market_1}: {e}')
                self.log.exception(f'[OPEN_TRADE] - Abort program. Unable to close base position with fail safe.')
                exit(1)

        else:
            self.order_dict['pair_status'] = 'LIVE'

        return self.order_dict, self.illiquid