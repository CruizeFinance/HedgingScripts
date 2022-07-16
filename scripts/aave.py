from scripts import dydx
from scripts import stgyapp
from scripts import interval
import math

class Aave(object):

    def __init__(self, config):
        assert config['debt'] == config['collateral'] * config['borrowed_pcg']
        self.market_price = config['market_price']
        self.interval_current = config['interval_current']
        self.entry_price = config['entry_price']
        self.collateral = config['collateral']
        self.borrowed_pcg = config['borrowed_pcg']
        self.debt = config['debt']
        self.ltv = config['ltv']
        self.price_to_ltv_limit = config['price_to_ltv_limit']
        self.lending_rate = config['lending_rate']
        self.borrowing_rate = config['borrowing_rate']
        self.USDC_status = config['USDC_status']
        # self.historical = pd.DataFrame()

    def collateral_usd(self):
        return self.collateral * self.market_price

    def fees_calc(self):
        return self.collateral * (self.lending_rate - self.borrowing_rate * self.borrowed_pcg)

    def ltv_calc(self):
        return self.debt / self.collateral_usd()

    def price_to_ltv_limit_calc(self, dydx_parameters):
        return self.entry_price  - ( self.dydx.Dydx(dydx_parameters).pnl(self.entry_price) + self.debt + self.fees_calc() ) / self.collateral

    # def add_historical(self, aave_parameters):
    #     self.historical.append(aave_parameters)

    def return_usdc(self):
        if self.usdc_status = True:
            # AAVE parameters
            self.stgy_status = False
            # self.entry_price = 0
            self.collateral = 0
            self.debt = 0
            self.ltv = 0

            self.price_to_ltv_limit = 0  # We have to define the criteria for this price
            self.lending_rate = 0
            self.borrowing_rate = 0
            # interval_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]

            aave_parameters = [self.market_price, self.interval_current.name, self.collateral, self.debt, self.ltv, self.price_to_ltv_limit,
                               self.lending_rate, self.borrowing_rate, self.stgy_status]
            # self.add_historical(aave_parameters)

    def borrow_usdc(self, interval_current):
        # AAVE parameters
        self.stgy_status = True
        self.entry_price = market_price
        self.collateral = stk
        self.debt = stk * self.entry_price * 0.2
        self.ltv = self.ltv_calc()

        self.price_to_ltv_limit = round(self.entry_price * 0.99, 3)  # We have to define the criteria for this price
        self.lending_rate = 0
        self.borrowing_rate = 0
        # I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]

        aave_parameters = [self.market_price, self.interval_current.name, self.collateral, self.debt, self.ltv, self.price_to_ltv_limit,
                           self.lending_rate, self.borrowing_rate, self.stgy_status]
        # self.add_historical(aave_parameters)

        interval_floor = interval.Interval(self.price_to_ltv_limit, p_floor, 'I_floor')
        interval_minus_infty = interval.Interval(-math.inf, self.price_to_ltv_limit, 'I_minus_infty')
        stgyapp.StgyApp().intervals['I_floor'] = interval_floor
        stgyapp.StgyApp().intervals['I_minus_infty'] = interval_minus_infty
        # intervals['I_floor'] = I_floor
        # I_minus_infty = [-math.inf, P_LTV_AAVE]
        # intervals['I_minus_infty'] = I_minus_infty
        return I_floor, aave_parameters

    def repay_aave(self, P, dydx_parameters):
        # p_AAVE, interval_AAVE, self.collateral, self.debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = aave_parameters
        dydx_ = dydx.Dydx(dydx_parameters)
        #
        fees = self.fees_calc(self.collateral, r_L, r_B)
        size_ETH_for_debt = (self.debt + fees) / (P - P_entry_DyDx)
        new_size_ETH = size_ETH - size_ETH_for_debt

        pnl_for_debt = pnl(size_ETH_for_debt, P)
        self.debt = self.debt + fees - pnl_for_debt

        size_ETH = new_size_ETH
        equity = Equity(size_ETH, P)
        notional = Notional(size_ETH, P)
        L = leverage(size_ETH, P)
        # Note that a negative self.debt is actually a profit
        # We update the parameters
        if self.debt > 0:
            AAVE_strategy_status = True
        else:
            AAVE_strategy_status = False

        aave_parameters = [market_price, interval_current.name, self.collateral, self.debt, self.ltv, self.price_to_ltv_limit,
                           self.lending_rate, self.borrowing_rate, self.stgy_status]
        dydx_parameters = [p_DyDx, interval_DyDx, size_ETH, equity, notional, L, short_status]
        # self.add_historical()
        return aave_parameters_aux, dydx_parameters_aux