import telebot
import pandas as pd
import dataframe_image as dfi
import json

from decouple import config 
from telebot import types
from dydx3 import Client
from web3 import Web3
from constants import (
    HOST,
    ETHEREUM_ADDRESS,
    DYDX_API_KEY,
    DYDX_API_SECRET,
    DYDX_PASSPHRASE,
    STARK_PRIVATE_KEY,
    HTTP_PROVIDER
)

# Initialise Telebot
API_KEY = config('TELEGRAM_INFO_TOKEN')
bot = telebot.TeleBot(API_KEY)

# Log into dYdX
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

# Messages
@bot.message_handler(commands=['start'])
def start(message):

    button_foo = types.InlineKeyboardButton("Account Balance 💰", callback_data='balance')
    button_bar = types.InlineKeyboardButton("Current Positions ⚡", callback_data='positions')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_foo)
    keyboard.add(button_bar)

    bot.send_message(message.chat.id, f"{'---- Welcome to dYdX Crypto Bot! ----':^6}\nSelect option:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "balance":
        account = client.private.get_account()
        raw = float(account.data['account']['freeCollateral'])
        free_collateral = '${:,.2f}'.format(raw)
        bot.send_message(call.message.chat.id,f"Free collateral: {free_collateral}")
    elif call.data == "positions":
        #pd.set_option("display.max_column", None)
        pd.set_option("display.max_colwidth", None)
        pd.set_option('display.width', -1)
        pd.set_option('display.max_rows', None)
        with open('bot_agents.json') as f:
                    trades = json.load(f)
        df = pd.DataFrame(trades)
        #df = pd.read_csv('coint_pairs.csv')
        df = pd.DataFrame(trades)
        df = df[['market_1','order_m1_side','market_2','order_m2_side','z_score','half_life']].rename(columns={'market_1':'Base',\
                                                                                                               'order_m1_side':'Side',\
                                                                                                               'market_2':'Quote',\
                                                                                                               'order_m2_side':'Side',\
                                                                                                               'z_score':'Z Score',\
                                                                                                               'half_life':'Half Life'})
        dfi.export(df, "table.png")
        bot.send_message(call.message.chat.id, "...Current open positions...")
        bot.send_photo(call.message.chat.id, open('table.png', 'rb'))

bot.infinity_polling()