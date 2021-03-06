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
from rb_order import robin_order


class robin_strategy:
    def __init__(self):
        self.param = {  # default parameters
            "short_window": 60,
            "long_window": 120,
            "signal_window": 60,
            "dollar_amt": 300,
        }
        self.data = robin_data()
        self.order = robin_order()

    def set_param(self, param):
        self.param = param
        print("parameters updated!")


    def momentum_ma_strategy(self, inputSymbol):
        short_window = self.param["short_window"]
        long_window = self.param["long_window"]
        dollar_amt = self.param["dollar_amt"]

        df = self.data.get_stock_historicals_df(inputSymbol)
        df["MA_fast"] = df["close_price"].rolling(short_window).mean()
        df["MA_slow"] = df["close_price"].rolling(long_window).mean()
        df["MA_fast_minus_slow"] = (
            df["MA_fast"] - df["MA_slow"]
        )  # positive: short trend is higher
        df["MA_signal"] = np.where(df["MA_fast_minus_slow"] > 0, 1, -1)

        ###################################
        # MA Strategy Begins
        ###################################

        ### Buy ###
        # filter1: two consecutive reverse sign
        if (
            df["MA_signal"][-1] == 1
            and df["MA_signal"][-2] == 1
            and df["MA_signal"][-3] == -1
        ):
            # if True:
            # filter 2: in fast ma line, last delta is larger than second last delta (momentum enlargement as a confirmation)
            if abs(df["MA_fast_minus_slow"][-1]) > abs(df["MA_fast_minus_slow"][-2]):
                # if True:
                open_positions = rs.build_holdings()
                # 0 position for SBUX -- can open position.
                if inputSymbol not in open_positions.keys():
                    # submit market buy
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print("buying signal", inputSymbol)
                    # self.market_buy_stock(inputSymbol,df,dollar_amt)
                    self.order.market_buy_stock_fractional(inputSymbol, dollar_amt)

                else:
                    print(
                        "buying signal, but ",
                        inputSymbol,
                        " position still exists, just hold, no more buying.",
                    )

        ### Sell ###
        # filter1: two consecutive reverse sign:
        elif (
            df["MA_signal"][-1] == -1
            and df["MA_signal"][-2] == -1
            and df["MA_signal"][-3] == 1
        ):
            # elif True:
            # filter 2: in fast ma line, last delta is larger than second last delta (momentum enlargement as a confirmation)
            if abs(df["MA_fast_minus_slow"][-1]) > abs(df["MA_fast_minus_slow"][-2]):
                # if True:
                open_positions = rs.build_holdings()
                # positive position for this symbol -- can close position.
                if inputSymbol in open_positions.keys():
                    # submit market sell
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print("selling signal", inputSymbol)
                    self.order.market_sell_stock_fractional(inputSymbol)
                else:
                    print(
                        "selling signal, but no ",
                        inputSymbol,
                        " position, just hold, no more selling",
                    )

        else:
            # print('stay calm')
            pass

    def momentum_ma_strategy_run(self, inputSymbols):
        while True:
            for symbol in inputSymbols:
                self.momentum_ma_strategy(symbol)
            time.sleep(10)

    def macd_strategy(self, inputSymbol):
        short_window = self.param["short_window"]
        long_window = self.param["long_window"]
        signal_window = self.param["signal_window"]
        dollar_amt = self.param["dollar_amt"]

        df = self.data.get_stock_historicals_df(inputSymbol)
        df["EMA_fast"] = df["close_price"].ewm(span=short_window).mean()
        df["EMA_slow"] = df["close_price"].ewm(span=long_window).mean()
        # positive: short trend is higher
        df["DIF"] = df["EMA_fast"] - df["EMA_slow"]
        df["DEA"] = df["DIF"].ewm(span=signal_window).mean()
        df["MACD"] = df["DIF"] - df["DEA"]

        # import talib
        # macd_tmp = talib.MACD(df['close_price'], fastperiod=10, slowperiod=30, signalperiod=12)

        bull_bear_flag = self.bull_bear_market_filter(inputSymbol)

        # long filter 1: bull market
        if bull_bear_flag == "bull":
            # long filter 2: macd from - to +, and value increased:
            if (
                df["MACD"][-1] > 0
                and df["MACD"][-2] > 0
                and df["MACD"][-3] < 0
                and abs(df["MACD"][-1]) > abs((df["MACD"][-2]))
            ):
                # long filtter 3: oversold
                if df["DIF"][-1] <= 0:  # TODO: 0 or what?
                    open_positions = rs.build_holdings()
                    # 0 position for SBUX -- can open position.
                    if inputSymbol not in open_positions.keys():
                        # submit market buy
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print("buying signal", inputSymbol)
                        # self.market_buy_stock(inputSymbol,df,dollar_amt)
                        self.order.market_buy_stock_fractional(inputSymbol, dollar_amt)
                    else:
                        print(
                            "buying signal, but ",
                            inputSymbol,
                            " position still exists, just hold, no more buying.",
                        )

            elif (
                df["MACD"][-1] < 0
                and df["MACD"][-2] < 0
                and df["MACD"][-3] > 0
                and abs(df["MACD"][-1]) > abs((df["MACD"][-2]))
            ):
                if df["DIF"][-1] >= 0:
                    open_positions = rs.build_holdings()
                    # positive position for this symbol -- can close position.
                    if inputSymbol in open_positions.keys():
                        # submit market sell
                        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print("selling signal", inputSymbol)
                        self.order.market_sell_stock_fractional(inputSymbol)
                    else:
                        print(
                            "selling signal, but no ",
                            inputSymbol,
                            " position, just hold, no more selling",
                        )
            else:
                # print('stay calm')
                pass

    def macd_strategy_run(self, inputSymbols):
        while True:
            for symbol in inputSymbols:
                self.macd_strategy(symbol)
            time.sleep(10)

    def check_crypto_position(self, inputSymbol):
        open_positions = rs.crypto.get_crypto_positions()
        quantity_available = 0
        for position in open_positions:
            if inputSymbol == position["currency"]["code"]:
                quantity_available = float(position["quantity_available"])
                return quantity_available
            else:
                pass
        return quantity_available

    def crypto_macd_strategy(self, inputSymbol):
        short_window = self.param["short_window"]
        long_window = self.param["long_window"]
        signal_window = self.param["signal_window"]
        dollar_amt = self.param["dollar_amt"]

        df = self.data.get_crypto_historicals_df(
            inputSymbol, interval="hour", span="week"
        )  # TODO need input
        df["EMA_fast"] = df["close_price"].ewm(span=short_window).mean()
        df["EMA_slow"] = df["close_price"].ewm(span=long_window).mean()
        # positive: short trend is higher
        df["DIF"] = df["EMA_fast"] - df["EMA_slow"]
        df["DEA"] = df["DIF"].ewm(span=signal_window).mean()
        df["MACD"] = df["DIF"] - df["DEA"]

        # import talib
        # macd_tmp = talib.MACD(df['close_price'], fastperiod=10, slowperiod=30, signalperiod=12)

        # long filter 1: macd from - to +, and value increased:
        if (
            df["MACD"][-1] > 0
            and df["MACD"][-2] > 0
            and df["MACD"][-3] < 0
            and abs(df["MACD"][-1]) > abs((df["MACD"][-2]))
        ):
            # long filtter 2: oversold
            if df["DIF"][-1] <= 0:  # TODO: 0 or what?
                # if True:
                quantity_available = self.check_crypto_position(inputSymbol)
                # 0 position for SBUX -- can open position.
                if quantity_available == 0:
                    # submit market buy
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print("buying signal", inputSymbol)
                    rs.orders.order_buy_crypto_by_price(
                        inputSymbol,
                        dollar_amt,
                        priceType="ask_price",
                        timeInForce="gtc",
                    )  # TODO: submit market buy crypto
                    # TODO: check order status!!!!!!!!!!!
                else:
                    print(
                        "buying signal, but ",
                        inputSymbol,
                        " position still exists, just hold, no more buying.",
                    )
        elif (
            df["MACD"][-1] < 0
            and df["MACD"][-2] < 0
            and df["MACD"][-3] > 0
            and abs(df["MACD"][-1]) > abs((df["MACD"][-2]))
        ):
            # elif True:
            if df["DIF"][-1] >= 0:
                # if True:
                quantity_available = self.check_crypto_position(inputSymbol)
                # positive position for this symbol -- can close position.
                if quantity_available > 0:
                    # submit market sell
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print("selling signal", inputSymbol)
                    # sell_dollar_amt = quantity_available * df['close_price'][-1]
                    rs.orders.order_sell_crypto_by_quantity(
                        inputSymbol,
                        quantity_available,
                        priceType="bid_price",
                        timeInForce="gtc",
                    )
                else:
                    print(
                        "selling signal, but no ",
                        inputSymbol,
                        " position, just hold, no more selling",
                    )

        # STOP LOSS negative diff
        elif (
            df["DIF"][-1] < 0
            and np.all(df["MACD"][::-1][:4] < 0)
            and df["MACD"][-4] > df["MACD"][-3]
            and df["MACD"][-3] > df["MACD"][-2]
            and df["MACD"][-2] > df["MACD"][-1]
        ):
            quantity_available = self.check_crypto_position(inputSymbol)
            # positive position for this symbol -- can close position.
            if quantity_available > 0:
                # submit market sell
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print("stop loss", inputSymbol)
                # sell_dollar_amt = quantity_available * df['close_price'][-1]
                rs.orders.order_sell_crypto_by_quantity(
                    inputSymbol,
                    quantity_available,
                    priceType="bid_price",
                    timeInForce="gtc",
                )
            else:
                print(
                    "stop loss, but no ",
                    inputSymbol,
                    " position, just hold, no more selling",
                )
        # STOP LOSS positive diff
        elif (
            df["DIF"][-1] > 0
            and np.all(df["MACD"][::-1][:6] < 0)
            and df["MACD"][-6] > df["MACD"][-5]
            and df["MACD"][-5] > df["MACD"][-4]
            and df["MACD"][-4] > df["MACD"][-3]
            and df["MACD"][-3] > df["MACD"][-2]
            and df["MACD"][-2] > df["MACD"][-1]
        ):
            quantity_available = self.check_crypto_position(inputSymbol)
            # positive position for this symbol -- can close position.
            if quantity_available > 0:
                # submit market sell
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print("stop loss", inputSymbol)
                # sell_dollar_amt = quantity_available * df['close_price'][-1]
                rs.orders.order_sell_crypto_by_quantity(
                    inputSymbol,
                    quantity_available,
                    priceType="bid_price",
                    timeInForce="gtc",
                )
            else:
                print(
                    "stop loss, but no ",
                    inputSymbol,
                    " position, just hold, no more selling",
                )
        else:
            # print('stay calm')
            pass

    def crypto_macd_strategy_run(self, inputSymbols):
        while True:
            for symbol in inputSymbols:
                self.crypto_macd_strategy(symbol)
            time.sleep(10)

    def bull_bear_market_filter(self, inputSymbol):
        short_window = self.param["short_window"]
        long_window = self.param["long_window"]
        signal_window = self.param["signal_window"]
        try:
            df = self.data.get_stock_historicals_df(inputSymbol, span="month")
        except:
            print("stock not found: try fetching as cryptocurrency:")
            try:
                df = self.data.get_crypto_historicals_df(
                    inputSymbol, interval="day", span="month", bound="24_7"
                )
            except:
                ValueError("cryptocurrency not found")
        # print("data fetched")

        df["EMA_fast"] = df["close_price"].ewm(span=short_window).mean()
        df["EMA_slow"] = df["close_price"].ewm(span=long_window).mean()
        # positive: short trend is higher
        df["DIF"] = df["EMA_fast"] - df["EMA_slow"]
        df["DEA"] = df["DIF"].ewm(span=signal_window).mean()
        df["MACD"] = df["DIF"] - df["DEA"]

        bull_bear_flag = "hold"
        if df["MACD"][-1] > 0 and df["MACD"][-2] > 0:
            bull_bear_flag = "bull"
        elif df["MACD"][-1] < 0 and df["MACD"][-2] < 0:
            bull_bear_flag = "bear"

        return bull_bear_flag

    def event_driven(self, inputSymbols):
        """stock headline NLP signal"""
        JNJ_news = rs.stocks.get_news("JNJ")
        title0 = JNJ_news[0]["title"]
        signal = self.headline_nlp_model(title0)
        return signal

    def headline_nlp_model(self, input):
        """load a pretrained embedding model"""
        return 0

    def grid_trading(self, inputSymbol):
        short_window = self.param["short_window"]
        long_window = self.param["long_window"]
        signal_window = self.param["signal_window"]
        dollar_amt = self.param["dollar_amt"]

        df = self.data.get_stock_historicals_df(inputSymbol)
        df["EMA_fast"] = df["close_price"].ewm(span=short_window).mean()
        df["EMA_slow"] = df["close_price"].ewm(span=long_window).mean()
        # positive: short trend is higher
        df["DIF"] = df["EMA_fast"] - df["EMA_slow"]
        df["DEA"] = df["DIF"].ewm(span=signal_window).mean()
        df["MACD"] = df["DIF"] - df["DEA"]
