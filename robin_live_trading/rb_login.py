import robin_stocks as rs
from rb_data import robin_data
from rb_strats import robin_strategy
from rb_order import robin_order

class robin_login:

    def __init__(self,username,password):
        rs.login(username, password)
        print('user login succeeded!')
        self.data = robin_data()
        self.strategy = robin_strategy()
        self.order = robin_order()

    def log_out(self):
        rs.logout()
        print('user logged out.')