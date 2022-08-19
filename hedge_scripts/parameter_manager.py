import math
import random
import numpy as np
import interval
from scipy.stats import norm
import pandas as pd


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, N_week, data_for_thresholds, floor):
        # stgy_instance.initialize_volatility_calculator()
        # We will take daily and weekly volatility. We assume our data is hourly, therefore rolling_number = 24, 7 * 24
        returns = np.around(data_for_thresholds['close'].pct_change().dropna(), 3)
        # stgy_instance.historical_data['returns'] = returns
        log_returns = np.log(data_for_thresholds['close']) - np.log(
            data_for_thresholds['close'].shift(1))
        # data_for_thresholds['log_returns'] = log_returns

        # ema log returns
        ewm_log_returns = log_returns[-N_week:].ewm(alpha=0.8, adjust=False)
        mean_ema_log_returns = round(ewm_log_returns.mean().mean() * 365, 3)
        std_ema_log_returns = round(ewm_log_returns.std().mean() * np.sqrt(365), 3)

        mu = mean_ema_log_returns / 365 * 24 * 60
        sigma = (std_ema_log_returns / np.sqrt(365)) * np.sqrt(24 * 60)

        top_pcg_open_close = 0.02
        number_of_sigmas_open_close = (top_pcg_open_close - mu) / sigma
        confidence_for_open_close = norm.cdf(number_of_sigmas_open_close)

        top_pcg_add_coll = 0.04
        number_of_sigmas_add_coll = (top_pcg_add_coll - mu) / sigma
        confidence_for_add_coll = norm.cdf(number_of_sigmas_add_coll)

        # factor_close_open = round(norm.ppf(0.90), 3)
        # factor_withdraw = round(norm.ppf(0.92), 3)
        # factor_add_coll = round(norm.ppf(0.95), 3)

        factor_close_open = number_of_sigmas_open_close
        factor_add_coll = number_of_sigmas_add_coll  # 15% more sigmas
        factor_withdraw = number_of_sigmas_add_coll # 15% more confidence


        p_open_short = floor * math.e**(mu + factor_close_open * sigma)
        p_close_short = p_open_short * math.e**(mu + factor_close_open * sigma)
        p_borrow_usdc_n_add_coll = p_close_short * math.e**(mu + factor_add_coll * sigma)
        p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * math.e**(mu + factor_withdraw * sigma)
        print(factor_close_open, factor_withdraw, factor_add_coll, mu, sigma)
        #
        # p_open_short = floor * (1 + (mu + 2*sigma))
        # p_close_short = p_open_short * (1 + (mu + 2*sigma))
        # p_borrow_usdc_n_add_coll = p_close_short * (1 + (mu + 3*sigma))
        # p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * (1 + (mu + 3*sigma))

        stgy_instance.target_prices_copy = stgy_instance.target_prices
        list_of_intervals = ["rtrn_usdc_n_rmv_coll_dydx",
                             "borrow_usdc_n_add_coll",
                             "close_short",
                             "open_short",
                             "floor"]
        list_of_trigger_prices = [p_rtrn_usdc_n_rmv_coll_dydx,
                                  p_borrow_usdc_n_add_coll,
                                  p_close_short,
                                  p_open_short,
                                  floor]
        # We define/update trigger prices
        for i in range(len(list_of_intervals)):
            interval_name = list_of_intervals[i]
            trigger_price = list_of_trigger_prices[i]
            stgy_instance.target_prices[interval_name] = trigger_price
        ###################################
        # data for plotting
        period = [data_for_thresholds.index[0].date(),
                  data_for_thresholds.index[-1].date()]
        return [factor_close_open, factor_withdraw, factor_add_coll], sigma, period

    @staticmethod
    def define_intervals(stgy_instance):
        stgy_instance.intervals = {"infty": interval.Interval(stgy_instance.target_prices['rtrn_usdc_n_rmv_coll_dydx'],
                                                              math.inf,
                                                              "infty", 0),
                                   }
        # By reading current names and values (instead of defining the list of names and values at hand) we can
        # use this method both for defining the thresholds the first time and for updating them every day
        names = list(stgy_instance.target_prices.keys())
        values = list(stgy_instance.target_prices.values())

        # We define/update thresholds
        for i in range(len(stgy_instance.target_prices) - 1):
            stgy_instance.intervals[names[i]] = interval.Interval(
                values[i + 1],
                values[i],
                names[i], i + 1)
        stgy_instance.intervals["minus_infty"] = interval.Interval(-math.inf,
                                                                   values[-1],
                                                                   "minus_infty",
                                                                   len(values))
        print(stgy_instance.intervals.keys())

    # function to assign interval_current to each market_price in historical data
    @staticmethod
    def load_intervals(stgy_instance):
        stgy_instance.historical_data["interval"] = [[0, 0]] * len(stgy_instance.historical_data["close"])
        stgy_instance.historical_data["interval_name"] = ['nan'] * len(stgy_instance.historical_data["close"])
        # for market_price in stgy_instance.historical_data["close"]:
        #     loc = list(stgy_instance.historical_data["close"]).index(market_price)
        #     # market_price = stgy_instance.historical_data["close"][loc]
        #     for i in list(stgy_instance.intervals.values()):
        #         if i.left_border < market_price <= i.right_border:
        #             stgy_instance.historical_data["interval"][loc] = i
        #             stgy_instance.historical_data["interval_name"][loc] = i.name

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
        stgy_instance.executed_actions = []
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
            # stgy_instance.append(action)

    @staticmethod
    def actions_to_take(stgy_instance, new_interval_current, interval_old):
        actions = []
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):
                actions.append(list(stgy_instance.intervals.keys())[i+1]) # when P goes up we execute the name of previous intervals
                # print(list(stgy_instance.intervals.keys())[i+1])
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):
                actions.append(list(stgy_instance.intervals.keys())[i])
        print(actions)
        return actions

    @staticmethod
    def simulate_fees(stgy_instance):
        # stgy_instance.gas_fees = round(random.choice(list(np.arange(1, 9, 0.5))), 6)

        # best case
        # stgy_instance.gas_fees = 1

        # stgy_instance.gas_fees = 3

        # stgy_instance.gas_fees = 6

        # worst case
        stgy_instance.gas_fees = 9

    @staticmethod
    def add_costs(stgy_instance):
        stgy_instance.total_costs = stgy_instance.total_costs + stgy_instance.aave.costs + stgy_instance.dydx.costs


if __name__ == '__main__':
    #######################################3
    # get historical data in seconds
    import requests
    from requests import Request
    from datetime import datetime
    import pandas as pd
    import numpy as np
    import json
    url = 'https://api.coinbase.com/v2/prices/BTC-USD/historic?2018-07-15T00:00:00-04:00'
    request = Request('GET', url)
    s = requests.Session()
    prepared = request.prepare()
    response = s.send(prepared).json()['data']['prices']
    historical_seconds = {'prices': [], 'date': []}
    for i in range(len(response)):
        item = response[i]
        historical_seconds['prices'].append(float(item['price']))
        historical_seconds['date'].append(datetime.strptime(item['time'], '%Y-%m-%dT%H:%M:%SZ'))
    historical_seconds = pd.DataFrame(historical_seconds['prices'],
                                      index=historical_seconds['date'],
                                      columns=['close']).iloc[::-1]
    historical_daily = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1d-data.csv")
    historical_hourly = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1h-data.csv")
    historical_minutes = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1m-data.csv")
    # assign data to stgy instance + define index as dates
    historical_data_daily = pd.DataFrame(historical_daily["close"], columns=['close'])
    historical_data_hourly = pd.DataFrame(historical_hourly["close"], columns=['close'])
    historical_data_minutes = pd.DataFrame(historical_minutes["close"], columns=['close'])

    ######################################################3
    # check historical 2min vol as benchmark to define add threshold
    manager = ParameterManager()
    # N_week = 1 * 1 * 7 * 24 * 60  # 7 days
    # data_for_thresholds = historical_data_minutes[:N_week].copy()  # First week of data

    log_returns_minutes = np.log(historical_minutes['close']) - np.log(
        historical_minutes['close'].shift(2))

    # ema log returns
    ewm_log_returns = log_returns_minutes.ewm(alpha=0.8, adjust=False)

    mean_ema_log_returns_mean_value = round(ewm_log_returns.mean().mean() * 365, 3)
    mean_ema_log_returns_max_value = round(ewm_log_returns.mean().max() * 365, 3)
    mean_ema_log_returns_min_value = round(ewm_log_returns.mean().min() * 365, 3)
    std_ema_log_returns_mean_value = round(ewm_log_returns.std().mean() * np.sqrt(365), 3)
    std_ema_log_returns_max_value = round(ewm_log_returns.std().max() * np.sqrt(365), 3)
    std_ema_log_returns_min_value = round(ewm_log_returns.std().min() * np.sqrt(365), 3)
    mu_2min_mean = round(mean_ema_log_returns_mean_value / 365 * 24 * 60, 3)
    mu_2min_max = round(mean_ema_log_returns_max_value / 365 * 24 * 60, 3)
    mu_2min_min = round(mean_ema_log_returns_min_value / 365 * 24 * 60, 3)
    sigma_2min_mean = round((std_ema_log_returns_mean_value / np.sqrt(365)), 3)
    sigma_2min_max = round((std_ema_log_returns_max_value / np.sqrt(365)), 3)
    sigma_2min_min = round((std_ema_log_returns_min_value / np.sqrt(365)), 3)
    std = ewm_log_returns.std()
    print(std[std==std.max()])
    print(historical_minutes['close'][9413-10:9413+10])

    print('Historical 2min mean vol:', sigma_2min_mean)
    print('Historical 2min max vol:', sigma_2min_max)
    print('Historical 2min min vol:', sigma_2min_min)

    ######################################################
    # check P_open / P_borrow to define ltv_0
    log_returns = np.log(historical_minutes['close']) - np.log(
        historical_minutes['close'].shift(1))
    # ema log returns
    ewm_log_returns = log_returns.ewm(alpha=0.8, adjust=False)
    mean_ema_log_returns = round(ewm_log_returns.mean().mean() * 365, 3)
    std_ema_log_returns = round(ewm_log_returns.std().mean() * np.sqrt(365), 3)

    mu = mean_ema_log_returns / 365 * 24 * 60
    sigma = (std_ema_log_returns / np.sqrt(365)) * np.sqrt(24 * 60)

    top_pcg_open_close = 0.02
    number_of_sigmas_open_close = (top_pcg_open_close - mu) / sigma
    confidence_for_open_close = norm.cdf(number_of_sigmas_open_close)

    top_pcg_add_coll = 0.04 # based on sigma_2min_max it should hold for ~ 4-5min
    number_of_sigmas_add_coll = (top_pcg_add_coll - mu) / sigma
    confidence_for_add_coll = norm.cdf(number_of_sigmas_add_coll)

    factor_close_open = number_of_sigmas_open_close
    factor_add_coll = number_of_sigmas_add_coll  # 15% more sigmas
    factor_withdraw = number_of_sigmas_add_coll  # 15% more confidence

    floor = 1500
    p_open_short = floor * math.e ** (mu + factor_close_open * sigma)
    p_close_short = p_open_short * math.e ** (mu + factor_close_open * sigma)
    p_borrow_usdc_n_add_coll = p_close_short * math.e ** (mu + factor_add_coll * sigma)
    p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * math.e ** (mu + factor_withdraw * sigma)
    print('p_open/p_borrow:', p_open_short/p_borrow_usdc_n_add_coll)
    print('mu, sigma, f_open, f_add:', mu, sigma, factor_close_open, factor_add_coll)



    factor = round(norm.ppf(0.65), 3)
    factor_close_open = round(norm.ppf(0.90), 3)
    factor_withdraw = round(norm.ppf(0.92), 3)
    factor_add_coll = round(norm.ppf(0.95), 3)


    floor = 1500

    # print(math.e ** (mu + factor * sigma))
    # print(mu + factor * sigma)
    # print(factor)

    mu = mu_2min_mean
    sigma = sigma_2min_mean
    top_pcg = 0.02
    number_of_sigmas = (top_pcg - mu) / sigma
    confidence_for_top_pcg = norm.cdf(number_of_sigmas)

    print(mu, sigma, factor)

    # print(confidence_for_top_pcg)
    # print(mu + number_of_sigmas * sigma)


    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 1, figsize=(21, 7))
    axs.plot(historical_minutes['close'], color='tab:blue', label='market price')
    # axs.plot(list(pnl_), label='DyDx pnl')

    floor = historical_minutes['close'].max() * 0.75
    p_open_short = floor * math.e ** (mu + factor_close_open * sigma)
    p_close_short = p_open_short * math.e ** (mu + factor_close_open * sigma)
    p_open_short_pcg = floor * math.e ** (mu + number_of_sigmas * sigma)
    p_close_short_pcg = p_open_short_pcg * math.e ** (mu + number_of_sigmas * sigma)
    # p_borrow_usdc_n_add_coll = p_close_short * math.e ** (mu + factor_add_coll * sigma)
    # p_rtrn_usdc_n_rmv_coll_dydx = p_borrow_usdc_n_add_coll * math.e ** (mu + factor_withdraw * sigma)



    # axs.axhline(y=p_rtrn_usdc_n_rmv_coll_dydx, color='black', linestyle='--',
    #             label='rtrn_usdc_n_rmv_coll_dydx')
    # axs.axhline(y=p_borrow_usdc_n_add_coll, color='darkgoldenrod', linestyle='--', label='borrow_usdc_n_add_coll')
    axs.axhline(y=p_close_short, color='olive', linestyle='--', label='close_short')
    axs.axhline(y=p_close_short_pcg, color='darkgoldenrod', linestyle='--', label='close_short_pcg')
    axs.axhline(y=p_open_short, color='darkred', linestyle='--', label='open_short')
    axs.axhline(y=p_open_short_pcg, color='black', linestyle='--', label='open_short_pcg')
    axs.axhline(y=floor, color='red', linestyle='--', label='floor')
    axs.grid()
    axs.legend(loc='lower left')
    plt.show()