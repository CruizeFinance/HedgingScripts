import math
import random
import numpy as np
from hedge_scripts import interval
# import time

class Aave(object):

    def __init__(self, config):
        # assert self.dydx_class_instance == isinstance(dydx)
        # assert config['debt'] == config['collateral_eth'] * config['borrowed_pcg']
        self.market_price = config['market_price']
        self.interval_current = config['interval_current']

        self.entry_price = config['entry_price']

        self.collateral_eth_initial = config['collateral_eth']
        self.collateral_eth = config['collateral_eth']
        self.collateral_usdc = config['collateral_usdc']

        self.reserve_margin_eth = 0
        self.reserve_margin_usdc = 0

        self.borrowed_percentage = config['borrowed_pcg']
        self.usdc_status = config['usdc_status']

        self.debt = config['debt']
        self.debt_initial = config['debt']

        self.ltv = config['ltv']
        self.price_to_ltv_limit = config['price_to_ltv_limit']

        self.lending_rate = 0
        self.lending_rate_hourly = 0
        self.interest_on_lending_eth = 0  # aggregated fees
        self.interest_on_lending_usd = 0
        self.lending_fees_eth = 0 # fees between last 2 prices
        self.lending_fees_usd = 0

        self.borrowing_rate = 0
        self.borrowing_rate_hourly = 0
        self.interest_on_borrowing = 0 # aggregated fees
        self.borrowing_fees = 0 # fees between last 2 prices

        self.lend_minus_borrow_interest = 0

        self.costs = 0
        # self.historical = pd.DataFrame()
        # self.dydx_class_instance = dydx_class_instance
        # self.staked_in_protocol = stk

    def collateral_usd(self):
        return self.collateral_eth * self.market_price

    def update_debt(self):
        """
        it requires having called borrowing_fees_calc() in order to use updated values of last earned fees
        """
        self.debt = self.debt + self.borrowing_fees

    def update_collateral(self):
        """
        it requires having called lending_fees_calc() in order to use updated values of last earned fees
        """
        self.collateral_eth = self.collateral_eth + self.lending_fees_eth
        self.collateral_usdc = self.collateral_usd()

    def track_lend_borrow_interest(self):
        """
        it requires having called borrowing_fees_calc() and lending_fees_calc()
        in order to use updated values of last earned fees
        """
        self.lend_minus_borrow_interest = self.interest_on_lending_usd - self.interest_on_borrowing

    def lending_fees_calc(self, freq):
        self.simulate_lending_rate()
        self.lending_rate_hourly = self.lending_rate / freq
        self.lending_fees_eth = self.collateral_eth * self.lending_rate_hourly
        self.lending_fees_usd = self.lending_fees_eth * self.market_price
        self.interest_on_lending_eth = self.interest_on_lending_eth + self.lending_fees_eth
        self.interest_on_lending_usd = self.interest_on_lending_usd + self.lending_fees_usd

    def borrowing_fees_calc(self, freq):
        self.simulate_borrowing_rate()
        self.borrowing_rate_hourly = self.borrowing_rate / freq
        self.borrowing_fees = self.collateral_eth * self.entry_price * self.borrowed_percentage * self.borrowing_rate_hourly
        self.interest_on_borrowing = self.interest_on_borrowing + self.borrowing_fees

    def simulate_lending_rate(self):
        # self.lending_rate = round(random.choice(list(np.arange(0.5/100, 1.5/100, 0.25/100))), 6)  # config['lending_rate']

        # best case
        # self.lending_rate = 1.5 / 100

        # worst case
        self.lending_rate = 0.5 / 100

    def simulate_borrowing_rate(self):
        # self.borrowing_rate = round(random.choice(list(np.arange(1.5/100, 2.5/100, 0.25/100))), 6)  # config['borrowing_rate']

        # best case
        # self.borrowing_rate = 1.5/100

        # worst case
        self.borrowing_rate = 2.5/100

    def ltv_calc(self):
        if self.collateral_usd() == 0:
            return 0
        else:
            return self.debt / self.collateral_usd()

    def price_to_liquidation(self, dydx_class_instance):
        return self.entry_price - (dydx_class_instance.pnl()
                                   + self.debt - self.lend_minus_borrow_interest) / self.collateral_eth

    def price_to_ltv_limit_calc(self):
        return round(self.entry_price * self.borrowed_percentage / self.ltv_limit(), 3)

    def buffer_for_repay(self):
        return 0.01

    def ltv_limit(self):
        return 0.5

    # Actions to take
    def return_usdc(self, new_market_price, new_interval_current, stgy_instance):
        gas_fees = stgy_instance.gas_fees
        time = 0
        if self.usdc_status:
            # simulate 2min delay for tx
            # update parameters
            # AAVE parameters
            self.usdc_status = False
            # self.collateral_eth = 0
            # self.collateral_usdc = 0
            self.debt = 0
            self.ltv = 0
            self.price_to_ltv_limit = 0
            # self.lending_rate = 0
            # self.borrowing_rate = 0

            # fees
            self.costs = self.costs + gas_fees

            time = 1
        return time

    def borrow_usdc(self, new_market_price, new_interval_current, stgy_instance):
        gas_fees = stgy_instance.gas_fees
        intervals = stgy_instance.intervals
        time = 0
        if not self.usdc_status:
            # AAVE parameters
            # update parameters
            self.usdc_status = True
            self.entry_price = self.market_price
            self.debt = self.collateral_eth_initial * self.borrowed_percentage * stgy_instance.target_prices['open_close']
            self.debt_initial = self.debt
            self.ltv = self.ltv_calc()

            # ltv_limit = 0.85
            # vol = stgy_instance.historical_data['vol']
            # benchmark_vol = 0.05
            # for i in range(5):
            #     if i*benchmark_vol < vol <= (i+1)*benchmark_vol:
            #         ltv_limit = 0.85 * 1/(i+1) = debt / coll(t) = debt / p_eth*coll = debt/p_eth_-1 * vol * coll
            self.price_to_ltv_limit = self.price_to_ltv_limit_calc()  # We have to define the criteria for this price
            # self.lending_rate = 0
            # self.borrowing_rate = 0

            # fees
            self.costs = self.costs + gas_fees

            price_floor = intervals['open_close'].left_border
            previous_position_order = intervals['open_close'].position_order
            intervals['floor'] = interval.Interval(self.price_to_ltv_limit, price_floor,
                                                     'floor', previous_position_order+1)
            intervals['minus_infty'] = interval.Interval(-math.inf, self.price_to_ltv_limit,
                                                           'minus_infty', previous_position_order+2)
            # simulate 2min delay for tx
            time = 1
        return time

    def repay_aave(self, new_market_price, new_interval_current,
                   stgy_instance):
        gas_fees = stgy_instance.gas_fees
        dydx_class_instance = stgy_instance.dydx
        # aave_class_instance = stgy_instance.aave
        # dydx_client_class_instance = stgy_instance.dydx_client
        #
        time = 0
        if self.usdc_status:
            # update parameters
            short_size_for_debt = self.debt / (self.market_price - dydx_class_instance.entry_price)
            new_short_size = dydx_class_instance.short_size - short_size_for_debt

            # pnl_for_debt = dydx_class_instance.pnl()
            # We have to repeat the calculations for pnl and notional methods, but using different size_eth
            pnl_for_debt = short_size_for_debt * (new_market_price - dydx_class_instance.entry_price)
            self.debt = self.debt - pnl_for_debt
            self.ltv = self.ltv_calc()

            self.price_to_ltv_limit = round(self.entry_price * (self.debt / self.collateral_usdc) / self.ltv_limit(), 3)
            self.costs = self.costs + gas_fees

            dydx_class_instance.market_price = self.market_price
            dydx_class_instance.interval_current = new_interval_current
            dydx_class_instance.short_size = new_short_size
            dydx_class_instance.notional = dydx_class_instance.notional_calc()
            dydx_class_instance.equity = dydx_class_instance.equity_calc()
            dydx_class_instance.leverage = dydx_class_instance.leverage_calc()
            dydx_class_instance.pnl = dydx_class_instance.pnl_calc()
            # dydx_class_instance.price_to_liquidation = \
            #     dydx_class_instance.price_to_liquidation_calc(dydx_client_class_instance)

            # fees
            # withdrawal_fees = pnl_for_debt * dydx_class_instance.withdrawal_fees
            dydx_class_instance.simulate_maker_taker_fees()
            notional_for_fees = abs(short_size_for_debt) * self.market_price
            dydx_class_instance.costs = dydx_class_instance.costs \
                                        + dydx_class_instance.maker_taker_fees * notional_for_fees \
                                        + pnl_for_debt * dydx_class_instance.withdrawal_fees

            # Note that a negative self.debt is actually a profit
            # We update the parameters
            if self.debt > 0:
                self.usdc_status = True
            else:
                self.usdc_status = False
            # simulate 2min delay for tx
            time = 1
        return time