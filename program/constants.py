from dydx3.constants import API_HOST_MAINNET, API_HOST_GOERLI
from decouple import config

# !!! SELECT MODE !!!
MODE = 'DEVELOPMENT'

# How long to run script in seconds
PERIOD_OF_TIME = 1200

# Close all positions
ABORT_ALL_POSITIONS = False

# FInd cointegrated pairs
FIND_CONIT_PARIS = True

# Place trades
PLACE_TRADES = True

# Manage exists
MANAGE_EXITS = True

# Resolution
RESOLUTION = '1HOUR'

# Stats window
WINDOW = 24

# Thresholds - Opening
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.5
USD_PER_TRADE = 50
USD_MIN_COLLATERAL = 1800

# Thresholds - Closing
CLOSE_AT_ZSCORE_CROSS = True

# Eth Address
ETHEREUM_ADDRESS = '0x6658373A6fDc6903c90d073AE9bC2f0fef4e4303'

# KEYS - PRODUCTION (MUST BE ON MAIN_NET ON DYDX)
STARK_PRIVATE_KEY_MAINNET = config('STARK_PRIVATE_KEY_MAINNET')
DYDX_API_KEY_MAINNET = config('DYDX_API_KEY_MAINNET')
DYDX_API_SECRET_MAINNET = config('DYDX_API_SECRET_MAINNET')
DYDX_PASSPHRASE_MAINNET = config('DYDX_PASSPHRASE_MAINNET')

# KEYS - DEVELOPMENT (MUST BE ON TEST_NET ON DYDX)
STARK_PRIVATE_KEY_TESTNET = config('STARK_PRIVATE_KEY_TESTNET')
DYDX_API_KEY_TESTNET= config('DYDX_API_KEY_TESTNET')
DYDX_API_SECRET_TESTNET = config('DYDX_API_SECRET_TESTNET')
DYDX_PASSPHRASE_TESTNET = config('DYDX_PASSPHRASE_TESTNET')

# KEYS - EXPORT
STARK_PRIVATE_KEY = STARK_PRIVATE_KEY_MAINNET if MODE == 'PRODUCTION' else STARK_PRIVATE_KEY_TESTNET
DYDX_API_KEY = DYDX_API_KEY_MAINNET if MODE == 'PRODUCTION' else DYDX_API_KEY_TESTNET
DYDX_API_SECRET = DYDX_API_SECRET_MAINNET if MODE == 'PRODUCTION' else DYDX_API_SECRET_TESTNET
DYDX_PASSPHRASE = DYDX_PASSPHRASE_MAINNET if MODE == 'PRODUCTION' else DYDX_PASSPHRASE_TESTNET

# HOST - EXPORT
HOST = API_HOST_MAINNET if MODE == 'PRODUCTION' else API_HOST_GOERLI

# HTTP PROVIDER
HTTP_PROVIDER_MAINNET = 'https://eth-mainnet.g.alchemy.com/v2/nCXL-lwBXG6pUH83C5L1kidBZKvgWHF_'
HTTP_PROVIDER_TESTNET = 'https://eth-goerli.g.alchemy.com/v2/cuhklr17kqY1L-Ch0WmS3TZcrmJigUtA'
HTTP_PROVIDER = HTTP_PROVIDER_MAINNET if MODE == 'PRODUCTION' else HTTP_PROVIDER_TESTNET