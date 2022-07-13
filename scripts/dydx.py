import math
import time
import matplotlib.pyplot as plt
import numpy as np

from scripts import aave


class Dydx(object):

    def __init__(self,
                 p=0,
                 p_entry=0,
                 short_size=0,
                 margin=0,
                 notional=0,
                 equity=0,
                 leverage=0,
                 pnl=0,
                 stgy_status=False):
        self.p_entry = p_entry
        self.market_price = p
        self.short_size = short_size
        self.margin = margin
        self.notional = notional
        self.equity = equity
        self.pnl = pnl
        self.leverage = leverage
        self.stgy_status = stgy_status
        self.historical = pd.DataFrame()

    def pnl_calc(self, p):
        return self.short_size * (p-self.p_entry)

    def notional_calc(self,p):
        return abs(self.short_size)*p

    def equity_calc(self,p):
        return self.margin + self.pnl(self.short_size,p)

    def leverage_calc(self, p):
        return notional(self.short_size,p) / equity(self.short_size, p)

    def p_to_cover_aave_debt_calc(self, aave_parameters, pcg_of_debt_to_cover):
        return self.p_entry + ( aave_parameters['debt'] + aave.Aave(aave_parameters).fees_function() ) * pcg_of_debt_to_cover / self.short_size

    def add_historical(self, dydc_parameters):
        self.historical.append(dydc_parameters)

    def remove_coll_DyDx(P, I_current, AAVE_parameters):
        short_status = False
        # DyDx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = AAVE_parameters
        P_entry_DyDx = 0
        size_ETH = 0
        margin = 0
        notional = Notional(size_ETH, P_entry_DyDx)
        equity = Equity(size_ETH, P_entry_DyDx)
        L = leverage(size_ETH, P_entry_DyDx)
        P_repay_debt = P_to_cover_AAVE_debt_function(size_ETH, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]
        DyDx_parameters = [P, I_current_name, size_ETH, equity, notional, L, P_repay_debt, short_status]

        return DyDx_parameters

    def add_coll_DyDx(P, I_current, AAVE_parameters):
        short_status = False
        # DyDx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = AAVE_parameters
        P_entry_DyDx = 0
        size_ETH = 0
        margin = Debt
        notional = Notional(size_ETH, P_entry_DyDx)
        equity = Equity(size_ETH, P_entry_DyDx)
        L = leverage(size_ETH, P_entry_DyDx)
        P_repay_debt = P_to_cover_AAVE_debt_function(size_ETH, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]
        DyDx_parameters = [P, I_current_name, size_ETH, equity, notional, L, P_repay_debt, short_status]

        return DyDx_parameters

    def open_short(P, I_current, AAVE_parameters):
        short_status = True
        # DyDx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = AAVE_parameters
        P_entry_DyDx = P
        size_ETH = -coll
        margin = Debt
        notional = Notional(size_ETH, P_entry_DyDx)
        equity = Equity(size_ETH, P_entry_DyDx)
        L = leverage(size_ETH, P_entry_DyDx)
        P_repay_debt = P_to_cover_AAVE_debt_function(size_ETH, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]
        DyDx_parameters = [P, I_current_name, size_ETH, equity, notional, L, P_repay_debt, short_status]

        return DyDx_parameters

    def close_short(P, I_current, DyDx_parameters):
        short_status = False
        # DyDx parameters
        # update profit parameters
        p_DyDx, interval_DyDx, size_ETH, equity, notional, L, P_repay_debt, short_status = DyDx_parameters
        pnl_position = pnl(size_ETH, P)
        equity = Equity(size_ETH, P)
        # close position
        size_ETH = 0
        notional = Notional(size_ETH, P)
        L = leverage(size_ETH, P)
        P_repay_debt = 0

        I_current_name = list(intervals.keys())[list(intervals.values()).index(I_current)]
        DyDx_parameters = [P, I_current_name, size_ETH, equity, notional, L, P_repay_debt, short_status]
        return DyDx_parameters