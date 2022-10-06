import math

import numpy as np

from hedge_scripts.Short_only.interval import Interval


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, slippage, vol, floor, pcg):
        mu = vol[0]
        sigma = vol[1]
        roof = floor * (1+pcg)
        start = (roof+floor)/2 # = floor (2+pcg)/2
        ##########################################################
        # We define the intervals
        list_of_intervals = ["roof",
                             "start",
                             "floor"]
        list_of_trigger_prices = [roof,
                                  start,
                                  floor]
        # We define/update trigger prices
        for i in range(len(list_of_intervals)):
            interval_name = list_of_intervals[i]
            trigger_price = list_of_trigger_prices[i]
            stgy_instance.trigger_prices[interval_name] = trigger_price

    @staticmethod
    def calc_vol(last_date, data):
        periods_for_vol = [6 * 30 * 24 * 60, 3 * 30 * 24 * 60, 1 * 30 * 24 * 60]
        last_six_months = data.loc[:last_date][-periods_for_vol[0]:]
        for i in range(len(periods_for_vol)):
            N = periods_for_vol[i]
            log_returns = np.log(last_six_months[-N:]['close']) - np.log(last_six_months[-N:]['close'].shift(1))
            globals()['sigma_' + str(i)] = log_returns.ewm(alpha=0.8, adjust=False).std().mean()
            globals()['mu_' + str(i)] = log_returns.ewm(alpha=0.8, adjust=False).mean().mean()
        mu = mu_0 * 0.1 + mu_1 * 0.3 + mu_2 * 0.6
        sigma = sigma_0 * 0.1 + sigma_1 * 0.3 + sigma_2 * 0.6
        vol = [mu, sigma]
        return vol

    @staticmethod
    # Checking and updating data
    def update_parameters(stgy_instance, new_market_price):
        # AAVE
        stgy_instance.aave.market_price = new_market_price
        # Before updating collateral and debt we have to calculate last earned fees + update interests earned until now
        # As we are using hourly data we have to convert anual rate interest into hourly interest, therefore freq=365*24
        stgy_instance.aave.lending_fees_calc(freq=365 * 24 * 60)
        stgy_instance.aave.borrowing_fees_calc(freq=365 * 24 * 60)
        # We have to execute track_ first because we need the fees for current collateral and debt values
        stgy_instance.aave.track_lend_borrow_interest()
        # stgy_instance.aave.update_costs() # we add lend_borrow_interest to costs
        stgy_instance.aave.update_debt()  # we add the last borrowing fees to the debt
        stgy_instance.aave.update_collateral()  # we add the last lending fees to the collateral and update both eth and usd values
        stgy_instance.aave.ltv = stgy_instance.aave.ltv_calc()

        # DYDX
        stgy_instance.dydx.market_price = new_market_price
        # Short updates
        stgy_instance.dydx.short_notional = stgy_instance.dydx.short_notional_calc()
        stgy_instance.dydx.short_equity = stgy_instance.dydx.short_equity_calc()
        stgy_instance.dydx.short_leverage = stgy_instance.dydx.short_leverage_calc()
        stgy_instance.dydx.short_pnl = stgy_instance.dydx.short_pnl_calc()
        # Long updates
        stgy_instance.dydx.long_notional = stgy_instance.dydx.long_notional_calc()
        stgy_instance.dydx.long_pnl = stgy_instance.dydx.long_pnl_calc()

    @staticmethod
    def reset_costs(stgy_instance):
        # We reset the costs in order to always start in 0
        stgy_instance.aave.costs = 0
        stgy_instance.dydx.short_costs = 0
        stgy_instance.dydx.long_costs = 0

    def find_scenario(self, stgy_instance, market_price, previous_market_price):
        self.simulate_fees(stgy_instance)
        roof = stgy_instance.trigger_prices['roof']
        start = stgy_instance.trigger_prices['start']
        floor = stgy_instance.trigger_prices['floor']
        # Case P crossing roof upwards: Close short
        if (previous_market_price <= roof) and (market_price >= roof):
            if stgy_instance.dydx.short_status:
                stgy_instance.dydx.close_short(stgy_instance)
        # Case P crossing start in any direction: Start both
        elif ((previous_market_price <= start) and (market_price >= start)) or ((previous_market_price >= start) and (market_price <= start)):
                stgy_instance.dydx.open_long(stgy_instance)
                stgy_instance.dydx.open_short(stgy_instance)
        # Case P crossing floor downwards: Close Long
        elif (previous_market_price >= floor) and (market_price <= floor):
            if stgy_instance.dydx.long_status:
                stgy_instance.dydx.close_long(stgy_instance)

    @staticmethod
    def simulate_fees(stgy_instance):
        # stgy_instance.gas_fees = round(random.choice(list(np.arange(1, 10, 0.5))), 6)

        # best case
        # stgy_instance.gas_fees = 1

        # stgy_instance.gas_fees = 3

        # stgy_instance.gas_fees = 6

        # worst case
        stgy_instance.gas_fees = 10

    @staticmethod
    def update_pnl(stgy_instance):
        stgy_instance.total_pnl = stgy_instance.total_pnl - stgy_instance.aave.costs - stgy_instance.dydx.short_costs - stgy_instance.dydx.long_costs + stgy_instance.aave.lending_fees_usd - stgy_instance.aave.borrowing_fees

    @staticmethod
    def add_costs(stgy_instance):
        stgy_instance.total_costs_from_aave_n_dydx = stgy_instance.total_costs_from_aave_n_dydx \
                                                     + stgy_instance.aave.costs + stgy_instance.dydx.short_costs +stgy_instance.dydx.long_costs