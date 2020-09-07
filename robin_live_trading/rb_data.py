import robin_stocks as rs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import datetime
import time
from rb_indicator import *


class robin_data():

    def __init__(self):
        self.param = {   #default parameters
            'short_window':60,
            'long_window':120,
            'signal_window':60,
            'dollar_amt':300,
                    }

    def get_stock_historicals_df(self,inputSymbols,span = 'week',bounds = 'regular'):

        span_check = ['day', 'week', 'month', '3month', 'year', '5year']
        bounds_check = ['extended', 'regular', 'trading']
        if span not in span_check:
            ValueError('ERROR: Span must be "day","week","month","3month","year",or "5year"')
        if bounds not in bounds_check:
            ValueError('ERROR: Bounds must be "extended","regular",or "trading"')
        if (bounds == 'extended' or bounds == 'trading') and span != 'day':
            ValueError('ERROR: extended and trading bounds can only be used with a span of "day"')

        res = rs.stocks.get_historicals(inputSymbols = inputSymbols, span = span,bounds = bounds)
        res_df = pd.DataFrame(res) 
        res_df.index = pd.to_datetime(res_df['begins_at']) + pd.Timedelta(hours=-4)  # convert to EST
        res_df.index = res_df.index.strftime("%m/%d-%H:%M")
        col_names = ['symbol','open_price','high_price','low_price','close_price','volume']
        price_cols = ['open_price','high_price','low_price','close_price','volume']
        res_df = res_df[col_names]
        res_df[price_cols] = res_df[price_cols].astype(float)
        return res_df


    def get_crypto_historicals_df(self,inputSymbol='BTC',interval = '15second',span = 'hour',bound='24_7'):

        interval_check = ['15second', '5minute', '10minute', 'hour', 'day', 'week']
        span_check = ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
        bounds_check = ['24_7', 'extended', 'regular', 'trading']
        if interval not in interval_check:
            ValueError('ERROR: Interval must be "15second","5minute","10minute","hour","day",or "week"')
        if span not in span_check:
            ValueError('ERROR: Span must be "hour","day","week","month","3month","year",or "5year"')
        if bound not in bounds_check:
            ValueError('ERROR: Bounds must be "24_7","extended","regular",or "trading"')
        if (bound == 'extended' or bound == 'trading') and span != 'day':
            ValueError('ERROR: extended and trading bounds can only be used with a span of "day"')
        res = rs.crypto.get_crypto_historical(inputSymbol,interval,span,bound)
        res_df = pd.DataFrame(res['data_points'])
        res_df.index = pd.to_datetime(res_df['begins_at']) + pd.Timedelta(hours=-4)  # convert to EST
        res_df.index = res_df.index.strftime("%m/%d-%H:%M:%S")
        col_names = ['open_price','high_price','low_price','close_price']
        res_df = res_df[col_names].astype(float)
        return res_df



    def plot_crypto_historicals(self,crypto_symbol,interval,span,bounds,figsize=(20,12), title='',subplots = 'MACD'):

        df = self.get_crypto_historicals_df(crypto_symbol,interval,span,bounds)
        print(len(df))
        short_window = self.param['short_window']
        long_window = self.param['long_window']

        fig, (ax1,ax2) = plt.subplots(nrows = 2,sharex = False,figsize = figsize)
        ax1.plot(df['close_price'], '-b', label='Price')
        ax1.plot(df['close_price'].rolling(short_window).mean(), '--r', label='MA_fast')
        ax1.plot(df['close_price'].rolling(long_window).mean(),'--y', label='MA_slow')

        if subplots == 'DTosc':
            df['dtosc_k'],df['dtosc_d'] = DTosc(df,(8,5,3,3))
            ax2.plot(df['dtosc_k'], '-b', label='unknown')
            ax2.plot(df['dtosc_d'], '-y', label='unknown2')

        elif subplots == 'MACD':
            df['DIF'],df['DEA'],df['MACD'] = MACD(df,self.param)
            ax2.bar(x = df['MACD'].index, height = df['MACD'].values,label = 'MACD')
            ax2.plot(df['DIF'],'--r',label = 'DIF')
            ax2.plot(df['DEA'],'--y',label = 'DEA')
            ax2.grid(True)
            ax2.legend(loc='best') # the plot evolves to the right

        else:
            ax2.bar(df['volume'].index,df['volume'].values,label='volume')

        max_yticks = 39
        xloc = plt.MaxNLocator(max_yticks)
        for ax in fig.axes:
            plt.sca(ax)
            plt.xticks(rotation=20)
            ax.xaxis.set_major_locator(xloc)
            ax.grid(True)
            ax.legend(loc='best')
        plt.title(title)
        plt.show()


    def plot_stock_historicals(self,stock_symbol,span,bounds,figsize=(20,12), title='',subplots = 'MACD'):
        
        df = self.get_stock_historicals_df(stock_symbol,span,bounds)
        print(len(df))
        short_window = self.param['short_window']
        long_window = self.param['long_window']

        fig, (ax1,ax2) = plt.subplots(nrows = 2,sharex = False,figsize = figsize)
        ax1.plot(df['close_price'], '-b', label='Price')
        ax1.plot(df['close_price'].rolling(short_window).mean(), '--r', label='MA_fast')
        ax1.plot(df['close_price'].rolling(long_window).mean(),'--y', label='MA_slow')

        if subplots == 'DTosc':
            df['dtosc_k'],df['dtosc_d'] = DTosc(df,(8,5,3,3))
            ax2.plot(df['dtosc_k'], '-b', label='unknown')
            ax2.plot(df['dtosc_d'], '-y', label='unknown2')

        elif subplots == 'MACD':
            df['DIF'],df['DEA'],df['MACD'] = MACD(df,self.param)
            ax2.bar(x = df['MACD'].index, height = df['MACD'].values,label = 'MACD')
            ax2.plot(df['DIF'],'--r',label = 'DIF')
            ax2.plot(df['DEA'],'--y',label = 'DEA')
            ax2.grid(True)
            ax2.legend(loc='best') # the plot evolves to the right

        else:
            ax2.bar(df['volume'].index,df['volume'].values,label='volume')

        max_yticks = 39
        xloc = plt.MaxNLocator(max_yticks)
        for ax in fig.axes:
            plt.sca(ax)
            plt.xticks(rotation=20)
            ax.xaxis.set_major_locator(xloc)
            ax.grid(True)
            ax.legend(loc='best')
        plt.title(title)
        plt.show()

        
    def live_plot_start(self,inputSymbol,crypto=False,interval = '15second',span = 'hour',bound = '24_7', figsize=(20,12),subplots = 'MACD'):
        
        if not crypto: 
            while (True): 
                clear_output(wait=True)
                print ("Current date and time : ")
                print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.plot_stock_historicals(inputSymbol,span,bound,figsize = figsize, title=inputSymbol,subplots = subplots)
                time.sleep(10)
        else:
            while (True):
                clear_output(wait=True)
                print ("Current date and time : ")
                print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.plot_crypto_historicals(inputSymbol,interval,span,bound,figsize = figsize, title=inputSymbol,subplots = subplots)
                time.sleep(10)
