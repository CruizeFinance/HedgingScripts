import math
import random
import numpy as np
import interval


class Dydx(object):

    def __init__(self, config):
        # assert aave_class == isinstance(aave)
        self.market_price = config['market_price']
        self.interval_current = config['interval_current']
        self.entry_price = config['entry_price']
        self.short_size = config['short_size']
        self.collateral = config['collateral']
        self.notional = config['notional']
        self.equity = config['equity']
        self.leverage = config['leverage']
        self.pnl = config['pnl']
        self.price_to_liquidation = config['price_to_liquidation']
        self.collateral_status = config['collateral_status']
        self.short_status = config['short_status']
        self.costs = config['costs']
        self.withdrawal_fees = 0.01/100
        self.funding_rates = 0
        # self.historical = pd.DataFrame()
        # self.aave_class_instance = aave_class_instance
        # self.staked_in_protocol = stk

    # auxiliary functions
    def pnl_calc(self):
        return self.short_size * (self.market_price-self.entry_price)

    def notional_calc(self):
        return abs(self.short_size)*self.market_price

    def equity_calc(self):
        return self.collateral + self.pnl_calc()

    def leverage_calc(self):
        if self.equity_calc() == 0:
            return 0
        else:
            return self.notional_calc() / self.equity_calc()

    def price_to_repay_aave_debt_calc(self, pcg_of_debt_to_cover, aave_class_instance):
        return self.entry_price \
               + (aave_class_instance.debt + aave_class_instance.fees_calc()) \
               * pcg_of_debt_to_cover / self.short_size

    @staticmethod
    def price_to_liquidation_calc(dydx_client_class_instance):
        return dydx_client_class_instance.dydx_margin_parameters["liquidation_price"]

    def add_funding_rates(self):
        self.simulate_funding_rates()
        self.costs = self.costs + self.funding_rates

    def simulate_funding_rates(self):
        self.funding_rates = random.choice(list(np.arange(-0.004/100, 0.004/100, 0.0005/100)))

    # Actions to take
    def remove_collateral_dydx(self, new_market_price, new_interval_current):
        # self.market_price = new_market_price
        # self.interval_current = new_interval_current
        if self.collateral_status:
            self.collateral_status = False
            self.short_status = False
            # dydx parameters
            self.entry_price = 0
            self.short_size = 0
            withdrawal_fees = self.collateral * self.withdrawal_fees
            self.collateral = 0
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            self.price_to_liquidation = 0

            # fees
            self.costs = self.costs + withdrawal_fees

    def add_collateral_dydx(self, new_market_price, new_interval_current,
                            gas_fees,
                            aave_class_instance):
        # self.market_price = new_market_price
        # self.interval_current = new_interval_current
        if not self.collateral_status:
            self.collateral_status = True
            self.short_status = False
            self.entry_price = 0
            self.short_size = 0
            self.collateral = aave_class_instance.debt
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            self.price_to_liquidation = 0

            # fees
            self.costs = self.costs + gas_fees

    def open_short(self, new_market_price, new_interval_current,
                   aave_class_instance, dydx_client_class_instance, intervals):
        # self.market_price = new_market_price
        # self.interval_current = new_interval_current
        if not self.short_status:
            self.collateral_status = True
            self.short_status = True
            # dydx parameters
            self.entry_price = self.market_price
            self.short_size = -aave_class_instance.collateral_eth
            self.collateral = aave_class_instance.debt
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = 0
            self.price_to_liquidation = self.price_to_liquidation_calc(dydx_client_class_instance)

            price_floor = intervals['open_short'].left_border
            floor_position = intervals['floor'].position_order
            price_to_repay_debt = self.price_to_repay_aave_debt_calc(1.5, aave_class_instance)
            price_to_ltv_limit = intervals['floor'].left_border
            if price_to_ltv_limit < price_to_repay_debt:
                intervals['floor'] = interval.Interval(price_to_repay_debt, price_floor,
                                                       'floor', floor_position)
                intervals['repay_aave'] = interval.Interval(price_to_ltv_limit, price_to_repay_debt,
                                                     'repay_aave', floor_position + 1)
                intervals['minus_infty'] = interval.Interval(-math.inf, price_to_ltv_limit,
                                                             'minus_infty', floor_position + 2)
            else:
                intervals['floor'] = interval.Interval(price_to_ltv_limit, price_floor,
                                                       'floor', floor_position)
                intervals['ltv_limit'] = interval.Interval(price_to_repay_debt, price_to_ltv_limit,
                                                            'repay_aave', floor_position + 1)
                intervals['minus_infty'] = interval.Interval(-math.inf, price_to_repay_debt,
                                                             'minus_infty', floor_position + 2)

    def close_short(self, new_market_price, new_interval_current):
        # self.market_price = new_market_price
        # self.interval_current = new_interval_current
        if self.short_status:
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            # We update short parameters after the calculation of pnl
            self.short_status = False
            self.short_size = 0
            self.price_to_liquidation = 0
