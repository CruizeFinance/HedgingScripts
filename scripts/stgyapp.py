import math
import json
from scripts import aave
from scripts import dydx
from scripts import interval


class StgyApp(object):

    def __init__(self, config):
        # We define intervals from target prices
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


    def launch(self, interval_old):
        self._run(market_price, interval_current, interval_old)

    def _run(self, market_price, interval_current, interval_old):
        actions = self.actions_to_take(interval_current, interval_old)
        for action in actions:
            if action in self.aave_features['methods']:
                self.aave.action(market_price, interval_current, self.dydx_features['attributes'])
            elif action in self.dydx_features['methods']:
                self.dydx.action(market_price, interval_current, self.aave_features['attributes'])

    def actions_to_take(self, interval_current, interval_old):
        actions = []
        if interval.Interval().is_lower(interval_old, interval_current):
            for i in reversed(range(interval_current.position_order, interval_old.position_order)):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))

        else:
            for i in range(interval_old.position_order + 1, interval_current.position_order + 1):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))
        return actions
    
if __name__ == '__main__':
    target_prices =
    target_prices_names = ['return_USDC', 'borrow_USDC', 'remove_collateral_dydx', 'add_collateral_dydx',
                           # 'put_limit_order',
                           'close_short', 'open_short']
    with open('/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json') as json_file:
        config = json.load(json_file)
    StgyApp(config).launch()
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