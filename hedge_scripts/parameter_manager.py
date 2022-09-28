import math
import random
import numpy as np
from scipy.stats import norm
import pandas as pd
import matplotlib.pyplot as plt

import interval


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, slippage, floor):
        p_open_close = floor * (1+slippage)
        ##########################################################
        # We define the intervals
        list_of_intervals = ["open_close",
                             "floor"]
        list_of_trigger_prices = [p_open_close,
                                  floor]
        # We define/update trigger prices
        for i in range(len(list_of_intervals)):
            interval_name = list_of_intervals[i]
            trigger_price = list_of_trigger_prices[i]
            stgy_instance.trigger_prices[interval_name] = trigger_price

    @staticmethod
    def define_intervals(stgy_instance):
        stgy_instance.intervals = {"infty": interval.Interval(stgy_instance.trigger_prices['open_close'],
                                                              math.inf,
                                                              "infty", 0),
                                   "open_close": interval.Interval(stgy_instance.trigger_prices['floor'],
                                                                   stgy_instance.trigger_prices['open_close'],
                                                                   "open_close", 1),
                                   "minus_infty": interval.Interval(-math.inf,
                                                                    stgy_instance.trigger_prices['floor'],
                                                                    "minus_infty", 2)}

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
        stgy_instance.dydx.interval_current = new_interval_current
        stgy_instance.dydx.notional = stgy_instance.dydx.notional_calc()
        stgy_instance.dydx.equity = stgy_instance.dydx.equity_calc()
        stgy_instance.dydx.leverage = stgy_instance.dydx.leverage_calc()
        stgy_instance.dydx.pnl = stgy_instance.dydx.pnl_calc()
        # stgy_instance.dydx.price_to_liquidation = stgy_instance.dydx.price_to_liquidation_calc(stgy_instance.dydx_client)

    def find_scenario(self, stgy_instance, new_market_price, new_interval_current, interval_old, index):
        actions = self.actions_to_take(stgy_instance, new_interval_current, interval_old)
        self.simulate_fees(stgy_instance)
        # We reset the costs in order to always start in 0
        stgy_instance.aave.costs = 0
        stgy_instance.dydx.costs = 0
        time = 0
        time_aave = 0
        time_dydx = 0
        for action in actions:
            # if action == "rtrn_usdc_n_rmv_coll_dydx":
            #     time = stgy_instance.dydx.remove_collateral_dydx(new_market_price, new_interval_current, stgy_instance)
            #     stgy_instance.aave.return_usdc(new_market_price, new_interval_current, stgy_instance)
            if action == "borrow_usdc_n_add_coll":
                time_aave = stgy_instance.aave.borrow_usdc(new_market_price, new_interval_current, stgy_instance)
                market_price = stgy_instance.historical_data["close"][index + time_aave]
                interval_current = stgy_instance.historical_data["interval"][index + time_aave]
                time_dydx = stgy_instance.dydx.add_collateral(market_price,
                                                              interval_current, stgy_instance)
                time_aave = 0
            elif action in stgy_instance.aave_features["methods"]:
                time_aave = getattr(stgy_instance.aave, action)(new_market_price, new_interval_current, stgy_instance)
            elif action in stgy_instance.dydx_features["methods"]:
                time_dydx = getattr(stgy_instance.dydx, action)(new_market_price, new_interval_current, stgy_instance)
            time += time_aave + time_dydx
            # print(stgy_instance.aave_features["methods"])
            # print(stgy_instance.dydx_features["methods"])
        return time
            # stgy_instance.append(action)

    @staticmethod
    def actions_to_take(stgy_instance, new_interval_current, interval_old):
        actions = []

        # Case P increasing
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):
                if list(stgy_instance.intervals.keys())[i+1] == 'open_close':
                    actions.append('close_short')
                else:
                    actions.append(list(stgy_instance.intervals.keys())[i+1]) # when P goes up we execute the name of previous intervals
                # print(list(stgy_instance.intervals.keys())[i+1])

        # Case P decreasing
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):
                if list(stgy_instance.intervals.keys())[i] == 'open_close':
                    actions.append('open_short')
                else:
                    actions.append(list(stgy_instance.intervals.keys())[i])
        # print(actions)
        return actions

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
        stgy_instance.total_pnl = stgy_instance.total_pnl - stgy_instance.aave.costs - stgy_instance.dydx.costs \
                                  + stgy_instance.aave.lending_fees_usd - stgy_instance.aave.borrowing_fees

    @staticmethod
    def add_costs(stgy_instance):
        stgy_instance.total_costs_from_aave_n_dydx = stgy_instance.total_costs_from_aave_n_dydx \
                                                     + stgy_instance.aave.costs + stgy_instance.dydx.costs

    @staticmethod
    def value_at_risk(data, method,  # T,
                      X):
        # exposure = abs(stgy_instance.dydx.short_size) # we are exposed to an amount equal to the size
        # window_to_use = 3 * 30 * 24 * 60 # 3 months of data
        # data = stgy_instance.historical_data[-window_to_use:]['close']
        # vol benchmark: daily version of last 3month 2min vol (mean std)
        if method == "parametric":
            """
            1) Normal returns assumption (deprecated):
            We assume portfolio value is normally distributed. Let's mu and sigma be the drift (SMA, EMA) and std of
            returns V_T/V_0.
                V_T / V_0 ~ N(mu*T, sigma^2*T)  --> V_T ~ V_0 * N(mu*T, sigma^2*T) = N(V_0 * mu*T, V_0^2 * sigma^2*T) 
                (mu*T = mu_T, sigma*T^1/2 = sigma_T, ie the value of mu and sigma expresses in the freq T)
            Then, using that 95% of values under normal dist falls between 1.96 sigmas, 
            we can say that with a 95% confidence 
                |V_T| < V_0 * mu*T +- 1.96 * V_0 * sigma * T^1/2
                        = V_0 * (mu*T +- 1.96 * sigma * T^1/2)
            2) Log-normal returns assumption:
            We assume portfolio value is log-normally distributed. Let's mu and sigma be the drift (SMA, EMA) and std of
            returns V_T/V_0.
            mu*T = mu_T, sigma*T^1/2 = sigma_T
                ln(V_T / V_0) ~ N((mu-sigma^2/2)*T, sigma^2*T) 
                --> ln V_T ~ ln V_0 + N((mu-sigma^2/2)*T, sigma^2*T)
                        = N(ln V_0 + (mu-sigma^2/2)*T, sigma^2*T)
            Then, using that 95% of values under normal dist falls between 1.96 sigmas, 
            we can say that with a 95% confidence 
                |ln V_T| < ln V_0 +(mu-sigma^2/2)*T +- 1.96 * sigma * T^1/2
                |V_T| < e^{ln V_0 +(mu-sigma^2/2)*T +- 1.96 * sigma * T^1/2} 
                        = V_0 * e^{(mu-sigma^2/2)*T +- 1.96 * sigma * T^1/2}
                        ~ V_0 * (1 + (mu-sigma^2/2)*T +- 1.96 * sigma * T^1/2) 
            In general, given a c-level X we can say the same using factor = F^-1(X) = norm.ppf(X)
            """
            # 2nd case
            log_returns = np.log(data) - np.log(data.shift(1))
            sigma = round(log_returns.ewm(alpha=0.8, adjust=False).std().mean(), 3)
            mu = round(log_returns.ewm(alpha=0.8, adjust=False).mean().mean(), 3)
            factor = round(norm.ppf(X), 3)
            var = (mu-sigma**2/2) + sigma * factor
            return var['close']
        elif method == "non_parametric":
            """
            We dont assume anything here. The idea will be to use past data for simulating different
            today's portfolio's value by taking
                change_i = price_i / price_{i-1} --> change on i-th day
                simulated_price_i = today_price * change_i 
                    --> simulated a new price assuming yesterday/today's change is equal to i-th/i-1-th's change 
                portf_value_i = exposure * simulated_price_i / today_price
                            [ = exposure * change_i ]
            Then, we calculate our potential profits/losses taking
                loss_i = exposure - portf_value_i 
                [ = exposure * (1 - simulated_price_i / today_price) 
                  = exposure * (1 - today_price * change_i / today_price 
                  = exposure * (1 - change_i) ]
                  i.e. we calculate the potential loss by comparing a portf value with actual exposure against
                  portf value with a different exposure (exposure * change_i)
            That will give us a dataset of daily losses and therefore a distribution for daily losses in the value of
            our portf.
            We take the VaR as the X-th percentile of this dist. That will be our 1-day VaR. In order to
            calculate N-day potential loss we take 1-day VaR * N^1/2.
            So we will be X% confident that we will not take a loss greater than this VaR estimate if market behaviour 
            is according to last data.
            Everywhere day can be changed by any other time freq, in our case by minutes.
            We repeat this for every new price, ie for every new data-set of last data to keep an 
            up to date VaR estimation.
            The estimate of VaR is the loss when we are at this 99th percentile point. When there are n observations 
            and k is an integer, the k/(n-1)-percentile is the observation ranked k + 1 of the list of losses ordered
            from lowest to highest losses.
            (Ex. n=501, X=99% --> 99th percentile --> k = (n-1)*0.99 = 495 --> The ﬁfth-highest loss)
            """
            changes = list(round(data.pct_change().dropna()['close'], 3))  # returns
            today = data.iloc[-1]['close']
            # print(today, changes)
            scenarios = []
            portf_value = []
            difference_in_portf_value = []
            difference_in_portf_value_pcg = []
            for i in range(len(changes)):
                scenarios.append(today * changes[i])
                # portf_value.append(exposure*scenarios[i]/today)
                # difference_in_portf_value.append(exposure - portf_value[i])
                difference_in_portf_value_pcg.append([changes[i], i])
            difference_in_portf_value_pcg.sort()
            plt.hist(changes)
            return difference_in_portf_value_pcg[-10:]

if __name__ == '__main__':
    pass