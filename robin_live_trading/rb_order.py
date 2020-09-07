import robin_stocks as rs




class robin_order:
    def __init__(self):
        pass 

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