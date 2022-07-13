from scripts import dydx
from scripts import stgyapp
import math

class Aave(object):

    def __init__(self,
                 p=0,
                 p_entry=0,
                 collateral=0,
                 borrowed_pcg = 0,
                 debt=0,
                 ltv=0,
                 p_ltv_limit=0,
                 lending_rate=0,
                 borrowing_rate=0,
                 stgy_status=False):
        assert debt == collateral * borrowed_pcg
        self.p_entry = p_entry
        self.market_price = p
        self.collateral = collateral
        self.borrowed_pcg = borrowed_pcg
        self.debt = debt
        self.ltv = ltv
        self.p_ltv_limit = p_ltv_limit
        self.lending_rate = lending_rate
        self.borrowing_rate = borrowing_rate
        self.stgy_status = stgy_status
        self.historical = pd.DataFrame()

    def collateral_usd(self, p):
        return self.collateral * p

    def fees_calc(self):
        return self.collateral * (self.lending_rate - self.borrowing_rate * self.borrowed_pcg)

    def ltv_calc(self, p):
        return self.debt / self.collateral_usd(self.collateral,p)

    def p_ltv_limit_calc(self, dydx_parameters):
        return self.p_entry  - ( self.dydx.Dydx(dydx_parameters).pnl(self.p_entry) + self.debt + self.fees_calc() ) / self.collateral

    def add_historical(self, aave_parameters):
        self.historical.append(aave_parameters)

    def close_stgy(self, p, interval_current):
        # AAVE parameters
        self.stgy_status = False
        # P_entry_AAVE = 0
        self.collateral = 0
        self.debt = 0
        self.ltv = 0

        self.p_ltv_limit = 0  # We have to define the criteria for this price
        self.lending_rate = 0
        self.borrowing_rate = 0
        # interval_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]

        aave_parameters = [p, interval_current.name, self.collateral, self.debt, self.ltv, self.p_ltv_limit,
                           self.lending_rate, self.borrowing_rate, self.stgy_status]
        self.add_historical(aave_parameters)

        # I_floor = [P_LTV_AAVE, P_floor]
        # intervals['I_floor'] = I_floor
        # I_minus_infty = [-math.inf, P_LTV_AAVE]
        # intervals['I_minus_infty'] = I_minus_infty
        # return AAVE_parameters

    def borrow_usdc(self, p, interval_current):
        # AAVE parameters
        self.stgy_status = True
        self.p_entry = p
        self.collateral = stk
        self.debt = stk * P_entry_AAVE * 0.2
        self.ltv = self.ltv_calc(self.p_entry)

        self.p_ltv_limit = round(self.p_entry * 0.99, 3)  # We have to define the criteria for this price
        self.lending_rate = 0
        self.borrowing_rate = 0
        # I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]

        aave_parameters = [p, interval_current.name, self.collateral, self.debt, self.ltv, self.p_ltv_limit,
                           self.lending_rate, self.borrowing_rate, self.stgy_status]
        self.add_historical(aave_parameters)

        interval_floor = interval.Interval(self.p_ltv_limit, p_floor, 'I_floor')
        interval_minus_infty = interval.Interval(-math.inf, self.p_ltv_limit, 'I_minus_infty')
        StgyApp.
        # intervals['I_floor'] = I_floor
        # I_minus_infty = [-math.inf, P_LTV_AAVE]
        # intervals['I_minus_infty'] = I_minus_infty
        return I_floor, AAVE_parameters

    def repay_aave(P, AAVE_parameters, DyDx_parameters):
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = AAVE_parameters
        p_DyDx, interval_DyDx, size_ETH, equity, notional, L, short_status = DyDx_parameters
        #
        fees = fees_function(coll, r_L, r_B)
        size_ETH_for_debt = (Debt + fees) / (P - P_entry_DyDx)
        new_size_ETH = size_ETH - size_ETH_for_debt

        pnl_for_debt = pnl(size_ETH_for_debt, P)
        Debt = Debt + fees - pnl_for_debt

        size_ETH = new_size_ETH
        equity = Equity(size_ETH, P)
        notional = Notional(size_ETH, P)
        L = leverage(size_ETH, P)
        # Note that a negative Debt is actually a profit
        # We update the parameters
        if Debt > 0:
            AAVE_strategy_status = True
        else:
            AAVE_strategy_status = False

        AAVE_parameters_aux = [p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status]
        DyDx_parameters_aux = [p_DyDx, interval_DyDx, size_ETH, equity, notional, L, short_status]

        return AAVE_parameters_aux, DyDx_parameters_aux