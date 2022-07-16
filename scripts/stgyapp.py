import math
import json
from scripts import aave
from scripts import dydx
from scripts import interval
from scripts import binance_client
from scripts import dydx_client

class StgyApp(object):

    def __init__(self, config):
        # We define intervals from target prices
        self.historical_data = None
        target_prices_values = config['target_prices']['values']
        target_prices_names = config['target_prices']['names']
        self.stk = config['stk']
        self.target_prices = dict(zip(target_prices_values,
                                      target_prices_names))
        self.intervals = {'infty': interval.Interval(target_prices_values[0],
                                                     math.inf,
                                                     'infty', 0),
                          'minus_infty': interval.Interval(-math.inf,
                                                           target_prices_values[-1],
                                                           'minus_infty', len(target_prices_values))
                          }
        for i in range(target_prices_values-1):
            self.intervals[ target_prices_names[i] ] = interval.Interval(target_prices_values[i+1],
                                                                         target_prices_values[i],
                                                                         target_prices_names[i], i+1)

        # We initialize aave and dydx classes instances
        self.aave = aave.Aave(config['initial_parameters']['aave'])
        self.dydx = dydx.Dydx(config['initial_parameters']['dydx'])

        # We load methods ans attributes for aave and dydx to use later
        self.aave_features = {'methods': [func for func in dir(self.aave)
                                          if callable(getattr(self.aave, func))],
                              'attributes': self.aave.__dict__.keys()}
        self.dydx_features = {'methods': [func for func in dir(self.dydx)
                                          if callable(getattr(self.dydx, func))],
                              'attributes': self.dydx.__dict__.keys()}

        # We create an attribute for historical data
        self.aave_historical_data = []
        self.dydx_historical_data = []

        # clients for data
        self.binance_client = binance_client.BinanceClient(config['binance_client'])
        self.dydx_client = dydx_client.DydxClient(config['dydx_client'])
        # self.historical_data =

    def launch(self, new_market_price, new_interval_current, new_interval_old):
        self.call_binance_data_loader()
        self.find_scenario(new_market_price, new_interval_current, new_interval_old)

    # Auxiliary functions
    def call_binance_data_loader(self):
        eth_historical = self.binance_client.get_all_binance(save=True)
        eth_prices = eth_historical[-2000:]['close']
        for i in range(len(eth_prices)):
            eth_prices[i] = float(eth_prices[i])
        self.historical_data = eth_prices

    def find_scenario(self, new_market_price, new_interval_current, new_interval_old):
        actions = self.actions_to_take(new_market_price, new_interval_old)
        for action in actions:
            if action in self.aave_features['methods']:
                if action == "borrow_usdc":
                    self.aave.borrow_usdc(new_market_price, new_interval_current, self.intervals)
                elif action == "repay_aave":
                    self.aave.repay_aave(new_market_price, new_interval_current, self.dydx, self.dydx_client)
                else:
                    getattr(self.aave, action)(new_market_price, new_interval_current, self.dydx)
            elif action in self.dydx_features['methods']:
                if action == "add_collateral_dydx":
                    self.dydx.add_collateral_dydx(new_market_price, new_interval_current, self.aave)
                elif action == "open_short":
                    self.dydx.open_short(new_market_price, new_interval_current, self.aave, self.dydx_client)
                else:
                    getattr(self.dydx, action)(new_market_price, new_interval_current, self.aave)
        self.aave_historical_data.append[self.aave.__dict__.keys()]
        self.dydx_historical_data.append[self.dydx.__dict__.keys()]

    def actions_to_take(self, new_interval_current, new_interval_old):
        actions = []
        if interval.Interval().is_lower(new_interval_old, new_interval_current):
            for i in reversed(range(new_interval_current.position_order, new_interval_old.position_order)):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))

        else:
            for i in range(new_interval_old.position_order + 1, new_interval_current.position_order + 1):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))
        return actions


if __name__ == '__main__':
    with open('/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json') as json_file:
        config = json.load(json_file)
    stgy = StgyApp(config)
    stgy.call_binance_data_loader()

    market_prices = stgy.historical_data
    intervals = list(stgy.intervals.values()) # esto se queda con la lista de las instancias de la clase intervalos

    summary = {'market_price': market_prices,
               'price_in_interval': [[0, 0]] * len(market_prices),
               'interval_name': ['0'] * len(market_prices)}

    for loc in range(len(summary['market_price'])):
        P = summary['market_price'][loc]
        for i in range(len(intervals)):
            if intervals[i].left_border < P <= intervals[i].right_border:
                summary['price_in_interval'][loc] = intervals[i]
                summary['interval_name'][loc] = intervals[i].name
    ######
    # run simulations
    interval_old = stgy.intervals['infty']
    aave_parameters = config['initial_parameters']['aave']
    dydx_parameters = config['initial_parameters']['dydx']
    for i in range(1, len(summary['market_price'][i - 1]) - 1):
        interval_previous = summary['price_in_interval'][i - 1]
        # P_previous = P[i-1]
        interval_current = summary['price_in_interval'][i]
        market_price = summary['market_price'][i]
        # We could pass the whole AAVE_historical_df, DyDx_historical_df as parameters for scenarios if necessary
        stgy.find_scenario(market_price, interval_current, interval_old)
        if interval_previous != interval_current:
            interval_old = interval_previous

####################################
# aux
# self.p_floor = 1140
# self.p_return_USDC = 1250
# self.p_borrow_USDC = 1200
# self.p_remove_collateral_dydx = 1190
# self.p_add_collateral_dydx = 1180
# self.p_put_limit_order = 1170
# self.p_floor_threshold = 1160
# self.p_close_short = 1150

# interval_infty = interval.Interval(self.target_prices['return_USDC'], math.inf,
#                                    'I_infty', 0)
# interval_close_aave = interval.Interval(self.target_prices['borrow_USDC'], self.target_prices['return_USDC'],
#                                         'I_return_USDC', 1)
# interval_add_coll_aave = interval.Interval(self.target_prices['remove_collateral_dydx'], self.target_prices['borrow_USDC'],
#                                            'I_borrow_USDC', 2)
# interval_remove_coll_dydx = interval.Interval(self.target_prices['add_collateral_dydx'], self.target_prices['remove_collateral_dydx'],
#                                               'I_remove_collateral_dydx', 3)
# interval_add_coll_dydx = interval.Interval(self.target_prices['put_limit_order'], self.target_prices['add_collateral_dydx'],
#                                            'I_add_collateral_dydx', 4)
# interval_put_limit_order = interval.Interval(self.target_prices['close_short'], self.target_prices['put_limit_order'],
#                                              'I_put_limit_order', 5)
# interval_close_short = interval.Interval(self.target_prices['floor_threshold'], self.target_prices['close_short'],
#                                          'I_close_short', 6)
# interval_open_short = interval.Interval(self.target_prices['floor'], self.target_prices['floor_threshold'],
#                                         'I_open_short', 7)
# interval_minus_infty = interval.Interval(-math.inf, self.target_prices['floor'],
#                                          'I_minus_infty', 8)
# interval_aave_LTV_limit = interval.Interval(float('nan'),float('nan'),'I_'


# self.intervals = {interval_infty.name: interval_infty,
#                   interval_close_aave.name: interval_close_aave,
#                   interval_add_coll_aave.name: interval_add_coll_aave,
#                   interval_remove_coll_dydx.name: interval_remove_coll_dydx,
#                   interval_add_coll_dydx.name: interval_add_coll_dydx,
#                   interval_put_limit_order.name: interval_put_limit_order,
#                   interval_close_short.name: interval_close_short,
#                   interval_open_short.name: interval_open_short,
#                   interval_minus_infty.name: interval_minus_infty}