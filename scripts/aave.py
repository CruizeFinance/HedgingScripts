from scripts import dydx
from scripts import stgyapp
from scripts import interval
import math


class Aave(object):

    def __init__(self, config):
        # assert self.dydx_class_instance == isinstance(dydx)
        # assert config['debt'] == config['collateral'] * config['borrowed_pcg']
        self.market_price = config['market_price']
        self.interval_current = config['interval_current']
        self.entry_price = config['entry_price']
        self.collateral = config['collateral']
        self.borrowed_pcg = config['borrowed_pcg']
        self.usdc_status = config['USDC_status']
        self.debt = config['debt']
        self.ltv = config['ltv']
        self.price_to_ltv_limit = config['price_to_ltv_limit']
        self.lending_rate = config['lending_rate']
        self.borrowing_rate = config['borrowing_rate']
        # self.historical = pd.DataFrame()
        # self.dydx_class_instance = dydx_class_instance
        # self.staked_in_protocol = stk

    def collateral_usd(self):
        return self.collateral * self.market_price

    def fees_calc(self):
        return self.collateral * (self.lending_rate - self.borrowing_rate * self.borrowed_pcg)

    def ltv_calc(self):
        return self.debt / self.collateral_usd()

    def price_to_ltv_limit_calc(self, dydx_class_instance):
        return self.entry_price - (dydx_class_instance.pnl()
                                   + self.debt + self.fees_calc()) / self.collateral

    # Actions to take
    def return_usdc(self, new_market_price, new_interval_current, dydx_class_instance):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if self.usdc_status:
            # AAVE parameters
            self.usdc_status = False
            self.collateral = 0
            self.debt = 0
            self.ltv = 0
            self.price_to_ltv_limit = 0
            self.lending_rate = 0
            self.borrowing_rate = 0

    def borrow_usdc(self, new_market_price, new_interval_current, intervals):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if not self.usdc_status:
            # AAVE parameters
            self.usdc_status = True
            self.entry_price = new_market_price
            self.debt = self.collateral * self.entry_price * self.borrowed_pcg
            self.ltv = self.ltv_calc()
            self.price_to_ltv_limit = round(self.entry_price * 0.99, 3)  # We have to define the criteria for this price
            self.lending_rate = 0
            self.borrowing_rate = 0

            price_floor = intervals['open_short'].left_border
            previous_position_order = intervals['open_short'].position_order
            intervals['I_floor'] = interval.Interval(self.price_to_ltv_limit, price_floor,
                                                     'I_floor', previous_position_order+1)
            intervals['I_minus_infty'] = interval.Interval(-math.inf, self.price_to_ltv_limit,
                                                           'I_minus_infty', previous_position_order+2)

    def repay_aave(self, new_market_price, new_interval_current, dydx_class_instance, dydx_client_class_instance):
        short_size = dydx_class_instance.short_size
        entry_price_dydx = dydx_class_instance.entry_price
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        #
        if self.usdc_status:
            fees = self.fees_calc()
            short_size_for_debt = (self.debt + fees) / (self.market_price - entry_price_dydx)
            new_short_size = short_size - short_size_for_debt

            pnl_for_debt = dydx_class_instance.pnl()
            self.debt = self.debt + fees - pnl_for_debt
            self.ltv = self.ltv_calc()
            self.price_to_ltv_limit = self.price_to_ltv_limit_calc()

            dydx_class_instance.market_price = new_market_price
            dydx_class_instance.interval_current = new_interval_current
            dydx_class_instance.short_size = new_short_size
            dydx_class_instance.notional = dydx_class_instance.notional_calc()
            dydx_class_instance.equity = dydx_class_instance.equity_calc()
            dydx_class_instance.leverage = dydx_class_instance.leverage_calc()
            dydx_class_instance.pnl = dydx_class_instance.pnl_calc()
            dydx_class_instance.price_to_liquidation = \
                dydx_class_instance.price_to_liquidation_calc(dydx_client_class_instance)

            # Note that a negative self.debt is actually a profit
            # We update the parameters
            if self.debt > 0:
                self.usdc_status = True
            else:
                self.usdc_status = False