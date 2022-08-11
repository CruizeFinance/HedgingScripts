import math
import random
import numpy as np
import interval


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, recent_data, floor):
        stgy_instance.initialize_volatility_calculator()
        # We will take daily and weekly volatility. We assume our data is hourly, therefore rolling_number = 24, 7 * 24
        returns = np.around(stgy_instance.historical_data['close'].pct_change().dropna(), 3)
        stgy_instance.historical_data['returns'] = returns
        log_returns = np.log(stgy_instance.historical_data['close']) - np.log(
            stgy_instance.historical_data['close'].shift(1))
        stgy_instance.historical_data['log_returns'] = log_returns
        N = 1 * 1 * 7
        # ema returns
        ewm_returns = stgy_instance.historical_data['returns'][-N:].ewm(alpha=0.8, adjust=False)
        # \mu annualized
        mean_ema_returns = round(ewm_returns.mean().mean() * 365, 3)
        # \sigma annualized
        std_ema_returns = round(ewm_returns.std().mean() * np.sqrt(365), 3)

        # ema log returns
        ewm_log_returns = stgy_instance.historical_data['log_returns'][-N:].ewm(alpha=0.8, adjust=False)
        mean_ema_log_returns = round(ewm_log_returns.mean().mean() * 365, 3)
        std_ema_log_returns = round(ewm_log_returns.std().mean() * np.sqrt(365), 3)

        # sma returns
        rolling_returns = stgy_instance.historical_data['returns'].rolling(window=14)
        mean_sma_returns = round(rolling_returns.mean() * 365, 3)
        std_sma_returns = round(rolling_returns.std().dropna().mean() * np.sqrt(365), 3)

        # sma log returns
        rolling_log_returns = stgy_instance.historical_data['log_returns'].rolling(window=14)
        mean_sma_log_returns = round(rolling_log_returns.mean().dropna().mean() * 365, 3)
        std_sma_log_returns = round(rolling_log_returns.std().dropna().mean() * np.sqrt(365), 3)


        mu = mean_ema_returns / 365 #* N
        sigma = (std_ema_returns / np.sqrt(365)) #* np.sqrt(N)
        p_open_short = floor * math.e**(mu + 1.5 * sigma)
        p_close_short = p_open_short * math.e**(mu + 1.5 * sigma)
        p_borrow_usdc_n_add_coll = p_close_short * math.e**(mu + 2 * sigma)
        p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * math.e**(mu + 2 * sigma)
        print(mu, sigma)
        #
        # p_open_short = floor * (1 + (mu + 2*sigma))
        # p_close_short = p_open_short * (1 + (mu + 2*sigma))
        # p_borrow_usdc_n_add_coll = p_close_short * (1 + (mu + 3*sigma))
        # p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * (1 + (mu + 3*sigma))

        stgy_instance.target_prices = {
            "rtrn_usdc_n_rmv_coll_dydx": p_rtrn_usdc_n_rmv_coll_dydx,
            "borrow_usdc_n_add_coll": p_borrow_usdc_n_add_coll,
            "close_short": p_close_short,
            "open_short": p_open_short,
            "floor": floor
        }
        return [1.5, 2], round(math.e**(mu + 2 * sigma),3)
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
        # for loc in range(len(stgy_instance.historical_data["close"])):
        for market_price in stgy_instance.historical_data["close"]:
            loc = list(stgy_instance.historical_data["close"]).index(market_price)
            # market_price = stgy_instance.historical_data["close"][loc]
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
            if action == "rtrn_usdc_n_rmv_coll_dydx":
                stgy_instance.dydx.remove_collateral_dydx(new_market_price, new_interval_current, stgy_instance)
                stgy_instance.aave.return_usdc(new_market_price, new_interval_current, stgy_instance)
            elif action == "borrow_usdc_n_add_coll":
                stgy_instance.aave.borrow_usdc(new_market_price, new_interval_current, stgy_instance)
                stgy_instance.dydx.add_collateral_dydx(new_market_price, new_interval_current, stgy_instance)
            elif action in stgy_instance.aave_features["methods"]:
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
        # stgy_instance.gas_fees = round(random.choice(list(np.arange(1, 9, 0.5))), 6)
        # stgy_instance.gas_fees = 1 # best case
        # stgy_instance.gas_fees = 3
        # stgy_instance.gas_fees = 6
        stgy_instance.gas_fees = 9 # worst case

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