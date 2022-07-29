import math
import random
import numpy as np
import interval


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, floor):
        stgy_instance.initialize_volatility_calculator()
        # We will take daily and weekly volatility. We assume our data is hourly, therefore rolling_number = 24, 7 * 24
        vol_sma_of_returns_daily = max(stgy_instance.volatility_calculator.get_sma_std_vol_of_returns(
            stgy_instance.historical_data, 1 * 24)['vol_sma_of_returns_respect_to_periods'].dropna())
        vol_sma_of_returns_weekly = np.mean(stgy_instance.volatility_calculator.get_sma_std_vol_of_returns(
            stgy_instance.historical_data, 7 * 24)['vol_sma_of_returns_respect_to_periods'])
        vol_ema_of_returns_daily = np.mean(stgy_instance.volatility_calculator.get_ema_std_vol_of_returns(
            stgy_instance.historical_data, 1 * 24)['vol_ema_of_returns_respect_to_periods'])
        vol_ema_of_returns_weekly = np.mean(stgy_instance.volatility_calculator.get_ema_std_vol_of_returns(
            stgy_instance.historical_data, 7 * 24)['vol_ema_of_returns_respect_to_periods'])

        vol_sma_of_prices_daily = max(stgy_instance.volatility_calculator.get_sma_std_vol_of_prices(
            stgy_instance.historical_data, 1 * 24)['vol_sma_of_prices_respect_to_periods'].dropna())
        vol_sma_of_prices_weekly = np.mean(stgy_instance.volatility_calculator.get_sma_std_vol_of_prices(
            stgy_instance.historical_data, 7 * 24)['vol_sma_of_prices_respect_to_periods'])
        vol_ema_of_prices_daily = np.mean(stgy_instance.volatility_calculator.get_ema_std_vol_of_prices(
            stgy_instance.historical_data, 1 * 24)['vol_ema_of_prices_respect_to_periods'])
        vol_ema_of_prices_weekly = np.mean(stgy_instance.volatility_calculator.get_ema_std_vol_of_prices(
            stgy_instance.historical_data, 7 * 24)['vol_ema_of_prices_respect_to_periods'])

        # vol = vol_sma_of_prices_daily
        # p_open_short = floor + vol
        # p_close_short = p_open_short + 1.5*vol
        # p_add_collateral_dydx = p_close_short + 3 * vol
        # # p_remove_collateral_dydx = p_add_collateral_dydx + 2 * vol)
        # p_borrow_usdc = p_add_collateral_dydx + 3 * vol
        # p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc + 3 * vol
        # # p_remove_collateral_dydx = p_rtrn_usdc_n_rmv_coll_dydx

        vol = vol_ema_of_prices_daily
        p_open_short = floor + vol
        p_close_short = p_open_short + 1.5 * vol
        p_add_collateral_dydx = p_close_short + 3 * vol
        # p_remove_collateral_dydx = p_add_collateral_dydx + 2 * vol
        p_borrow_usdc = p_add_collateral_dydx + 3 * vol
        p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc + 3 * vol
        # p_remove_collateral_dydx = p_rtrn_usdc_n_rmv_coll_dydx


        stgy_instance.target_prices = {
            "rtrn_usdc_n_rmv_coll_dydx": p_rtrn_usdc_n_rmv_coll_dydx,
            "borrow_usdc": p_borrow_usdc,
            # "remove_collateral_dydx": p_remove_collateral_dydx,
            "add_collateral_dydx": p_add_collateral_dydx,
            "close_short": p_close_short,
            "open_short": p_open_short,
            "floor": floor
        }

    @staticmethod
    def define_intervals(stgy_instance):
        stgy_instance.intervals = {"infty": interval.Interval(stgy_instance.target_prices['rtrn_usdc_n_rmv_coll_dydx'],
                                                              math.inf,
                                                              "infty", 0),
                                   }
        names = list(stgy_instance.target_prices.keys())
        values = list(stgy_instance.target_prices.values())
        for i in range(len(stgy_instance.target_prices) - 1):
            stgy_instance.intervals[names[i]] = interval.Interval(
                values[i + 1],
                values[i],
                names[i], i + 1)
        stgy_instance.intervals["minus_infty"] = interval.Interval(-math.inf,
                                                                   values[-1],
                                                                   "minus_infty",
                                                                   len(values))

    # function to assign interval_current to each market_price in historical data
    @staticmethod
    def load_intervals(stgy_instance):
        stgy_instance.historical_data["interval"] = [[0, 0]] * len(stgy_instance.historical_data["close"])
        stgy_instance.historical_data["interval_name"] = ['nan'] * len(stgy_instance.historical_data["close"])
        for loc in range(len(stgy_instance.historical_data["close"])):
            market_price = stgy_instance.historical_data["close"][loc]
            for i in list(stgy_instance.intervals.values()):
                if i.left_border < market_price <= i.right_border:
                    stgy_instance.historical_data["interval"][loc] = i
                    stgy_instance.historical_data["interval_name"][loc] = i.name


    @staticmethod
    # Checking and updating data
    def update_parameters(stgy_instance, new_market_price, new_interval_current):
        # AAVE
        stgy_instance.aave.market_price = new_market_price
        stgy_instance.aave.interval_current = new_interval_current
        # Before updating collateral and debt we have to calculate last earned fees + update interests earned until now
        # As we are using hourly data we have to convert anual rate interest into hourly interest, therefore freq=365*24
        stgy_instance.aave.lending_fees_calc(freq=365 * 24)
        stgy_instance.aave.borrowing_fees_calc(freq=365 * 24)
        # We have to execute track_ first because we need the fees for current collateral and debt values
        stgy_instance.aave.track_lend_borrow_interest()
        stgy_instance.aave.update_debt()  # we add the last borrowing fees to the debt
        stgy_instance.aave.update_collateral()  # we add the last lending fees to the collateral and update both eth and usd values
        stgy_instance.aave.ltv = stgy_instance.aave.ltv_calc()

        # DYDX
        stgy_instance.dydx.market_price = new_market_price
        stgy_instance.dydx.interval_current = new_interval_current
        stgy_instance.dydx.notional = stgy_instance.dydx.notional_calc()
        stgy_instance.dydx.equity = stgy_instance.dydx.equity_calc()
        stgy_instance.dydx.leverage = stgy_instance.dydx.leverage_calc()
        stgy_instance.dydx.pnl = stgy_instance.dydx.pnl_calc()
        stgy_instance.dydx.price_to_liquidation = stgy_instance.dydx.price_to_liquidation_calc(stgy_instance.dydx_client)

    def find_scenario(self, stgy_instance, new_market_price, new_interval_current, interval_old):
        actions = self.actions_to_take(stgy_instance, new_interval_current, interval_old)
        self.simulate_fees(stgy_instance)
        # We reset the costs in order to always start in 0
        stgy_instance.aave.costs = 0
        stgy_instance.dydx.costs = 0
        for action in actions:
            if action in stgy_instance.aave_features["methods"]:
                getattr(stgy_instance.aave, action)(new_market_price, new_interval_current, stgy_instance)
            elif action in stgy_instance.dydx_features["methods"]:
                getattr(stgy_instance.dydx, action)(new_market_price, new_interval_current, stgy_instance)

    @staticmethod
    def actions_to_take(stgy_instance, new_interval_current, interval_old):
        actions = []
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):
                actions.append(list(stgy_instance.intervals.keys())[i+1]) # when P goes up we execute the name of previous intervals
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):
                actions.append(list(stgy_instance.intervals.keys())[i])
        return actions

    @staticmethod
    def simulate_fees(stgy_instance):
        stgy_instance.gas_fees = round(random.choice(list(np.arange(1, 9, 0.5))), 6)

    @staticmethod
    def add_costs(stgy_instance):
        stgy_instance.total_costs = stgy_instance.total_costs + stgy_instance.aave.costs + stgy_instance.dydx.costs


# if action == "rtn_usdc_n_rmv_coll_dydx":
            #     stgy_instance.aave.return_usdc(new_market_price, new_interval_current, stgy_instance)
            #     stgy_instance.dydx.remove_collateral_dydx(new_market_price, new_interval_current)
            # elif action in stgy_instance.aave_features["methods"]:
            #     if action == "borrow_usdc":
            #         stgy_instance.aave.borrow_usdc(new_market_price, new_interval_current, stgy_instance)
            #     elif (action == "repay_aave") | (action == "ltv_limit"):
            #         stgy_instance.aave.repay_aave(new_market_price, new_interval_current,
            #                              stgy_instance)
            # elif action in stgy_instance.dydx_features["methods"]:
            #     if action == "add_collateral_dydx":
            #         stgy_instance.dydx.add_collateral_dydx(new_market_price, new_interval_current,
            #                                       stgy_instance)
            #     elif action == "open_short":
            #         stgy_instance.dydx.open_short(new_market_price, new_interval_current,
            #                              stgy_instance)
            #     elif action == "close_short":
            #         stgy_instance.dydx.close_short(new_market_price, new_interval_current,
            #                               stgy_instance)
            #     else:
            #         getattr(stgy_instance.dydx, action)(new_market_price, new_interval_current, stgy_instance)