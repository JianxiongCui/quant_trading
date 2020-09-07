import numpy as np
# import robin_stocks as rs


# param = {   #default parameters
#             'short_window':60,
#             'long_window':120,
#             'signal_window':60,
#             'dollar_amt':300,
#         }

def hurst_f(input_df, lags_to_test=20):  
    # interpretation of return value
    # hurst < 0.5 - input_ts is mean reverting
    # hurst = 0.5 - input_ts is effectively random/geometric brownian motion
    # hurst > 0.5 - input_ts is trending
    tau = []
    lagvec = []  
    #  Step through the different lags  
    for lag in range(2, lags_to_test):  
        #  produce price difference with lag  
        pp = input_df[lag:].values - input_df[:-lag].values
        #  Write the different lags into a vector  
        lagvec.append(lag)  
        #  Calculate the variance of the differnce vector  
        tau.append(np.sqrt(np.std(pp)))  
    #  linear fit to double-log graph (gives power)  
    m = np.polyfit(np.log10(lagvec), np.log10(tau), 1)  
    # calculate hurst  
    hurst = m[0]*2
    print(hurst)
    return hurst  


def RSI(input_df,window_length): #relative strength index
    df = input_df[:]
    df['delta'] = df['close_price'].diff()
    df['up'] = np.where(df['delta']>0,df['delta'],0)
    df['down'] = np.where(df['delta']<0,df['delta'],0)
    df['rolling_up'] = df['up'].rolling(window_length).mean()
    df['rolling_down'] = df['down'].abs().rolling(window_length).mean()  # TODO: rolling vs ewm
    RS = df['rolling_up']/df['rolling_down']
    RSI = 100.0 - (100.0 / (1.0 + RS))
    df['RSI']=RSI
    return RSI


def DTosc(input_df,settings=(13,8,5,5)): #8 ,5,3,3   13,8,5,5   21,13,8,8   34,21,13,13
    df = input_df[:]
    a,b,c,d = settings
    rsi = RSI(df,a)
    e = rsi.rolling(b).max()
    f = rsi.rolling(b).min()
    sto_rsi = 100.0 * ((rsi - f)/ (e - f))
    dtosc_k = sto_rsi.rolling(c).mean()
    dtosc_d = dtosc_k.rolling(d).mean()
    return dtosc_k,dtosc_d

def MACD(input_df,param):
    df = input_df[:]
    short_window = param['short_window']
    long_window = param['long_window']
    signal_window = param['signal_window']

    df['EMA_fast'] = df['close_price'].ewm(span = short_window).mean()
    df['EMA_slow'] = df['close_price'].ewm(span = long_window).mean() 
    df['DIF'] = df['EMA_fast'] - df['EMA_slow']  # positive: short trend is higher
    df['DEA'] = df['DIF'].ewm(span = signal_window).mean()
    df['MACD'] = df['DIF'] - df['DEA']
    return df['DIF'],df['DEA'],df['MACD']