import robin_stocks as rs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import datetime
import time
from copy import deepcopy
import talib
from rb_indicator import *
from rb_data import robin_data


class robin_strategy():

    def __init__(self):
        self.param = {   #default parameters
            'short_window':60,
            'long_window':120,
            'signal_window':60,
            'dollar_amt':300,
        }
        self.data = robin_data()

    def set_param(self,param):
        self.param = param
        print('parameters updated!')

    def market_buy_stock(self,inputSymbol,df,dollar_amt):
        '''
        if cash < 0： try dollar_amt order
        if cash > 0:  try dollar_amt_order
        '''
        share_quantity_1 = int(dollar_amt/df['close_price'][0]) # if cash_available >= dollar_amt else int(cash_available/df['close_price'][0])
        order_try_1 = rs.orders.order_buy_market(symbol = inputSymbol,quantity = share_quantity_1)
        if 'id' not in order_try_1.keys(): # order failed
            share_quantity_2 = int(order_try_1['detail'].split()[4])
            if share_quantity_2 < share_quantity_1: # buy fewer shares
                order_try_2 = rs.orders.order_buy_market(symbol = inputSymbol,quantity = share_quantity_2)
                if 'id' in order_try_2.keys():
                    print('market buy ',share_quantity_2, inputSymbol)
                else:
                    print('fail to market buy ',inputSymbol)
            else:
                print('fail to market buy ',inputSymbol)
        else:
            print('market buy ',share_quantity_1, inputSymbol)
        return 0


    def market_sell_stock(self,inputSymbol):

        ## submit market sell
        holdings = rs.build_holdings()[inputSymbol]
        share_quantity = int(float(holdings['quantity']))
        rs.orders.order_sell_market(symbol = inputSymbol,quantity = share_quantity)
        ## TODO:deal with day-trade error: just leave it failed
        print('market sell ',share_quantity, inputSymbol)

        return 0


    def momentum_ma_strategy(self,inputSymbol):
        short_window = self.param['short_window']
        long_window = self.param['long_window']
        dollar_amt = self.param['dollar_amt']

        df = self.data.get_stock_historicals_df(inputSymbol)
        df['MA_fast'] = df['close_price'].rolling(short_window).mean()
        df['MA_slow'] = df['close_price'].rolling(long_window).mean() 
        df['MA_fast_minus_slow'] = df['MA_fast'] - df['MA_slow']  ## positive: short trend is higher
        df['MA_signal'] = np.where(df['MA_fast_minus_slow']>0,1,-1)
        
        ###################################
        ##  MA Strategy Begins
        ###################################

        ### Buy ###
        ## filter1: two consecutive reverse sign
        if df['MA_signal'][-1] == 1 and df['MA_signal'][-2] == 1 and df['MA_signal'][-3] == -1: 
        # if True:
            ## filter 2: in fast ma line, last delta is larger than second last delta (momentum enlargement as a confirmation) 
            if  abs(df['MA_fast_minus_slow'][-1]) > abs(df['MA_fast_minus_slow'][-2]):
            # if True:
                open_positions = rs.build_holdings()
                if inputSymbol not in open_positions.keys():  ## 0 position for SBUX -- can open position. 
                    ## submit market buy
                    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print('buying signal', inputSymbol)
                    self.market_buy_stock(inputSymbol,df,dollar_amt)

                else: 
                    print('buying signal, but ',inputSymbol,' position still exists, just hold, no more buying.')

        ### Sell ###
        ## filter1: two consecutive reverse sign:
        elif df['MA_signal'][-1] == -1 and df['MA_signal'][-2] == -1 and df['MA_signal'][-3] == 1: 
        # elif True:
            ## filter 2: in fast ma line, last delta is larger than second last delta (momentum enlargement as a confirmation) 
            if  abs(df['MA_fast_minus_slow'][-1]) > abs(df['MA_fast_minus_slow'][-2]):
            # if True:
                open_positions = rs.build_holdings()
                if inputSymbol in open_positions.keys():  ## positive position for this symbol -- can close position.
                    ## submit market sell
                    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print('selling signal', inputSymbol)
                    self.market_sell_stock(inputSymbol)
                else: 
                    print('selling signal, but no ',inputSymbol,' position, just hold, no more selling') 
    
        else:    
            # print('stay calm')
            pass

    def momentum_ma_strategy_run(self,inputSymbols):
        while(True):
            for symbol in inputSymbols:
                self.momentum_ma_strategy(symbol)
            time.sleep(10)

    def macd_strategy(self,inputSymbol):
        short_window = self.param['short_window']
        long_window = self.param['long_window']
        signal_window = self.param['signal_window']
        dollar_amt = self.param['dollar_amt']

        df = self.data.get_stock_historicals_df(inputSymbol)
        df['EMA_fast'] = df['close_price'].ewm(span = short_window).mean()
        df['EMA_slow'] = df['close_price'].ewm(span = long_window).mean() 
        df['DIF'] = df['EMA_fast'] - df['EMA_slow']  # positive: short trend is higher
        df['DEA'] = df['DIF'].ewm(span = signal_window).mean()
        df['MACD'] = df['DIF'] - df['DEA']

        # import talib 
        # macd_tmp = talib.MACD(df['close_price'], fastperiod=10, slowperiod=30, signalperiod=12)

        bull_bear_flag = self.bull_bear_market_filter(inputSymbol)

        # long filter 1: bull market 
        if bull_bear_flag == 'bull':
            # long filter 2: macd from - to +, and value increased: 
            if df['MACD'][-1] > 0 and df['MACD'][-2] > 0 and df['MACD'][-3] < 0 and abs(df['MACD'][-1]) > abs((df['MACD'][-2])):
                # long filtter 3: oversold
                if df['DIF'][-1] <= 0: ## TODO: 0 or what?
                    open_positions = rs.build_holdings()
                    if inputSymbol not in open_positions.keys():  ## 0 position for SBUX -- can open position. 
                        ## submit market buy
                        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print('buying signal', inputSymbol)
                        self.market_buy_stock(inputSymbol,df,dollar_amt)
                    else: 
                        print('buying signal, but ',inputSymbol,' position still exists, just hold, no more buying.')

            elif df['MACD'][-1] < 0 and df['MACD'][-2] < 0 and df['MACD'][-3] > 0 and abs(df['MACD'][-1]) > abs((df['MACD'][-2])):
                if df['DIF'][-1] >= 0:
                    open_positions = rs.build_holdings()
                    if inputSymbol in open_positions.keys():  ## positive position for this symbol -- can close position.
                        ## submit market sell
                        print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print('selling signal', inputSymbol)
                        self.market_sell_stock(inputSymbol)
                    else: 
                        print('selling signal, but no ',inputSymbol,' position, just hold, no more selling') 
            else:    
                # print('stay calm')
                pass

    def macd_strategy_run(self,inputSymbols):
        while(True):
            for symbol in inputSymbols:
                self.macd_strategy(symbol)
            time.sleep(10)



    def check_crypto_position(self,inputSymbol):
        open_positions = rs.crypto.get_crypto_positions()
        quantity_available = 0
        for position in open_positions:
            if inputSymbol == position['currency']['code']:
                quantity_available = float(position['quantity_available'])
                return quantity_available
            else:
                pass
        return quantity_available

    
    def crypto_macd_strategy(self,inputSymbol):
        short_window = self.param['short_window']
        long_window = self.param['long_window']
        signal_window = self.param['signal_window']
        dollar_amt = self.param['dollar_amt']

        df = self.data.get_crypto_historicals_df(inputSymbol,interval='hour',span='week') ## TODO need input
        df['EMA_fast'] = df['close_price'].ewm(span = short_window).mean()
        df['EMA_slow'] = df['close_price'].ewm(span = long_window).mean() 
        df['DIF'] = df['EMA_fast'] - df['EMA_slow']  # positive: short trend is higher
        df['DEA'] = df['DIF'].ewm(span = signal_window).mean()
        df['MACD'] = df['DIF'] - df['DEA']

        # import talib 
        # macd_tmp = talib.MACD(df['close_price'], fastperiod=10, slowperiod=30, signalperiod=12)

        # long filter 1: macd from - to +, and value increased: 
        if df['MACD'][-1] > 0 and df['MACD'][-2] > 0 and df['MACD'][-3] < 0 and abs(df['MACD'][-1]) > abs((df['MACD'][-2])):
            # long filtter 2: oversold
            if df['DIF'][-1] <= 0: ## TODO: 0 or what?
            # if True:
                quantity_available = self.check_crypto_position(inputSymbol)
                if quantity_available == 0 :  ## 0 position for SBUX -- can open position. 
                    ## submit market buy
                    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print('buying signal', inputSymbol)
                    rs.orders.order_buy_crypto_by_price(inputSymbol,dollar_amt,priceType='ask_price',timeInForce='gtc') ## TODO: submit market buy crypto
                    ## TODO: check order status!!!!!!!!!!!
                else: 
                    print('buying signal, but ',inputSymbol,' position still exists, just hold, no more buying.')
        elif df['MACD'][-1] < 0 and df['MACD'][-2] < 0 and df['MACD'][-3] > 0 and abs(df['MACD'][-1]) > abs((df['MACD'][-2])):
        # elif True:    
            if df['DIF'][-1] >= 0:
            # if True:
                quantity_available = self.check_crypto_position(inputSymbol)
                if quantity_available >0 :  ## positive position for this symbol -- can close position.
                    ## submit market sell
                    print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print('selling signal', inputSymbol)
                    # sell_dollar_amt = quantity_available * df['close_price'][-1]
                    rs.orders.order_sell_crypto_by_quantity(inputSymbol,quantity_available,priceType='bid_price',timeInForce='gtc')       
                else: 
                    print('selling signal, but no ',inputSymbol,' position, just hold, no more selling') 

        ## STOP LOSS negative diff
        elif df['DIF'][-1]<0 and np.all(df['MACD'][::-1][:4] < 0) and df['MACD'][-4] > df['MACD'][-3] and df['MACD'][-3] > df['MACD'][-2] and df['MACD'][-2] > df['MACD'][-1]:
            quantity_available = self.check_crypto_position(inputSymbol)
            if quantity_available >0 :  ## positive position for this symbol -- can close position.
                ## submit market sell
                print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print('stop loss', inputSymbol)
                # sell_dollar_amt = quantity_available * df['close_price'][-1]
                rs.orders.order_sell_crypto_by_quantity(inputSymbol,quantity_available,priceType='bid_price',timeInForce='gtc')       
            else:       
                print('stop loss, but no ',inputSymbol,' position, just hold, no more selling') 
        ## STOP LOSS positive diff
        elif df['DIF'][-1]>0 and np.all(df['MACD'][::-1][:6] < 0) and df['MACD'][-6] > df['MACD'][-5] and df['MACD'][-5] > df['MACD'][-4] and df['MACD'][-4] > df['MACD'][-3] and df['MACD'][-3] > df['MACD'][-2] and df['MACD'][-2] > df['MACD'][-1]:
            quantity_available = self.check_crypto_position(inputSymbol)
            if quantity_available >0 :  ## positive position for this symbol -- can close position.
                ## submit market sell
                print (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print('stop loss', inputSymbol)
                # sell_dollar_amt = quantity_available * df['close_price'][-1]
                rs.orders.order_sell_crypto_by_quantity(inputSymbol,quantity_available,priceType='bid_price',timeInForce='gtc')       
            else:    
                print('stop loss, but no ',inputSymbol,' position, just hold, no more selling') 
        else :    
            # print('stay calm')
            pass

    def crypto_macd_strategy_run(self,inputSymbols):
        while(True):
            for symbol in inputSymbols:
                self.crypto_macd_strategy(symbol)
            time.sleep(10)


    def bull_bear_market_filter(self,inputSymbol):
        short_window = self.param['short_window']
        long_window = self.param['long_window']
        signal_window = self.param['signal_window']
        try:
            df = self.get_stock_historicals_df(inputSymbol,span = 'month')
        except:
            print("stock not found: try fetching as cryptocurrency:")
            try:
                df = self.get_crypto_historicals_df(inputSymbol,interval = 'day',span = 'month',bound='24_7')
            except:
                ValueError("cryptocurrency not found")
        print("data fetched")    

        df['EMA_fast'] = df['close_price'].ewm(span = short_window).mean()
        df['EMA_slow'] = df['close_price'].ewm(span = long_window).mean() 
        df['DIF'] = df['EMA_fast'] - df['EMA_slow']  # positive: short trend is higher
        df['DEA'] = df['DIF'].ewm(span = signal_window).mean()
        df['MACD'] = df['DIF'] - df['DEA']

        bull_bear_flag = 'hold'
        if df['MACD'][-1] >0 and df['MACD'][-2] >0:
            bull_bear_flag = 'bull'
        elif df['MACD'][-1] <0 and df['MACD'][-2] <0:
            bull_bear_flag = 'bear'
        
        return bull_bear_flag

    
    def event_driven(self,inputSymbols):
        JNJ_news = rs.stocks.get_news('JNJ')
        title0 = JNJ_news[0]['title']
        


        
        
