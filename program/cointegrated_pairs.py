import pandas as pd
import numpy as np
import statsmodels.api as sm

from statsmodels.tsa.stattools import coint
from constants import MAX_HALF_LIFE, WINDOW

def calc_half_life(spread):
    '''
    Calculate the half life of two market pairs.

    :param spread: Spread of the two assets
    :return half_life: Half life of the assets
    '''

    df_spread = pd.DataFrame(spread, columns=['spread'])
    spread_lag = df_spread.spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    half_life = round(-np.log(2)/res.params[1],0)

    return half_life

def calc_z_score(spread):
    '''
    Calculate the z score of the spread.

    :param spread: Spread of the two assets
    :return z_score: Z-score of the spread (standardised)
    '''

    spread_series = pd.Series(spread)
    mean = spread_series.rolling(center=False, window=WINDOW).mean()
    std = spread_series.rolling(center=False, window=WINDOW).std()
    x = spread_series.rolling(center=False, window=1).mean()
    z_score = (x-mean)/std

    return z_score

def calc_coint(series_1, series_2):
    '''
    Calcualte cointegration flag.

    :param series_1: Series of first market pair
    :param series_2: Series of second market pair
    :return coint_flag: Boolean to determine if coint or not
    :return hedge_ratio: Hedge ratio between series 1 & 2
    :return half_life: Half life of two series
    '''

    series_1 = np.array(series_1).astype(np.float)
    series_2 = np.array(series_2).astype(np.float)

    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_val = coint_res[1]
    critical_val = coint[2][1]

    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]

    spread = series_1 - (hedge_ratio*series_2)
    half_life = calc_half_life(spread)

    t_check = coint_t < critical_val
    coint_flag = 1 if p_val < 0.05 and t_check else 0

    return coint_flag, hedge_ratio, half_life