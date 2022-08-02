import os
import pygsheets
import matplotlib.pyplot as plt
from scipy.stats import norm
import csv
import pandas as pd
import numpy as np

import interval


class DataDamperNPlotter:
    @staticmethod
    def write_data(stgy_instance, aave_instance, dydx_instance,
                   new_interval_previous, interval_old, mkt_price_index,
                   sheet=False):
        data_aave = []
        data_dydx = []
        aave_wanted_keys = [
            "market_price",
            "interval_current",
            "entry_price",
            "collateral_eth",
            "usdc_status",
            "debt",
            "ltv",
            "lending_rate",
            "interest_on_lending_usd",
            "borrowing_rate",
            "interest_on_borrowing",
            "lend_minus_borrow_interest",
            "costs"]

        for i in range(len(aave_instance.__dict__.values())):
            if list(aave_instance.__dict__.keys())[i] in aave_wanted_keys:
                # print(list(aave_instance.__dict__.keys())[i])
                if isinstance(list(aave_instance.__dict__.values())[i], interval.Interval):
                    data_aave.append(str(list(aave_instance.__dict__.values())[i].name))
                    data_aave.append(new_interval_previous.name)
                    data_aave.append(interval_old.name)
                else:
                    data_aave.append(str(list(aave_instance.__dict__.values())[i]))
        for i in range(len(dydx_instance.__dict__.values())):
            if isinstance(list(dydx_instance.__dict__.values())[i], interval.Interval):
                data_dydx.append(str(list(dydx_instance.__dict__.values())[i].name))
                data_dydx.append(new_interval_previous.name)
                data_dydx.append(interval_old.name)
            else:
                data_dydx.append(str(list(dydx_instance.__dict__.values())[i]))
        # We add the index number of the appareance of market price in historical_data.csv order to find useful test values quicker
        data_aave.append(stgy_instance.gas_fees)
        data_aave.append(stgy_instance.total_costs)
        data_aave.append(mkt_price_index)
        data_dydx.append(stgy_instance.gas_fees)
        data_dydx.append(stgy_instance.total_costs)
        data_dydx.append(mkt_price_index)
        # print(data_aave, list(dydx_instance.__dict__.keys()))
        if sheet == True:
            gc = pygsheets.authorize(service_file=
                                     '/home/agustin/Git-Repos/HedgingScripts/files/stgy-1-simulations-e0ee0453ddf8.json')
            sh = gc.open('aave/dydx simulations')
            sh[0].append_table(data_aave, end=None, dimension='ROWS', overwrite=False)
            sh[1].append_table(data_dydx, end=None, dimension='ROWS', overwrite=False)
        else:
            with open('/home/agustin/Git-Repos/HedgingScripts/files/aave_results.csv', 'a') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_aave)
            with open('/home/agustin/Git-Repos/HedgingScripts/files/dydx_results.csv', 'a',
                      newline='', encoding='utf-8') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_dydx)

    @staticmethod
    def delete_results():
        file_aave = '/home/agustin/Git-Repos/HedgingScripts/files/aave_results.csv'
        file_dydx = '/home/agustin/Git-Repos/HedgingScripts/files/dydx_results.csv'
        if (os.path.exists(file_aave) and os.path.isfile(file_aave)):
            os.remove(file_aave)
        if (os.path.exists(file_dydx) and os.path.isfile(file_dydx)):
            os.remove(file_dydx)

    @staticmethod
    def add_header():
        aave_headers = [
            "market_price",
            "I_current",
            "I_previous",
            "I_old",
            "entry_price",
            "collateral_eth",
            "usdc_status",
            "debt",
            "ltv",
            "lending_rate",
            "interest_on_lending_usd",
            "borrowing_rate",
            "interest_on_borrowing",
            "lend_minus_borrow_interest",
            "costs",
            "gas_fees",
            "total_costs",
            "index_of_mkt_price"]
        dydx_headers = [
            "market_price",
            "I_current",
            "I_previous",
            "I_old",
            "entry_price",
            "short_size",
            "collateral",
            "notional",
            "equity",
            "leverage",
            "pnl",
            "price_to_liquidation",
            "collateral_status",
            "short_status",
            "withdrawal_fees",
            "funding_rates",
            "maker_taker_fees",
            "costs",
            "gas_fees",
            "total_costs",
            "index_of_mkt_price"]
        with open('/home/agustin/Git-Repos/HedgingScripts/files/aave_results.csv', 'a') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(aave_headers)
        with open('/home/agustin/Git-Repos/HedgingScripts/files/dydx_results.csv', 'a',
                  newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(dydx_headers)

    @staticmethod
    def historical_parameters_data(aave_instance, dydx_instance):
        aave_df = pd.DataFrame(aave_instance.historical_data, columns=list(aave_instance.__dict__.keys()))
        dydx_df = pd.DataFrame(dydx_instance.historical_data, columns=list(dydx_instance.__dict__.keys()))
        return {"aave_df": aave_df,
                "dydx_df": dydx_df}

    @staticmethod
    def plot_data(stgy_instance):
        # colors https://datascientyst.com/full-list-named-colors-pandas-python-matplotlib/
        fig, axs = plt.subplots(1, 1, figsize=(21, 7))
        axs.plot(stgy_instance.historical_data['close'], color='tab:blue', label='market price')
        # axs.plot(list(pnl_), label='DyDx pnl')
        p_rtrn_usdc_n_rmv_coll_dydx = stgy_instance.target_prices['rtrn_usdc_n_rmv_coll_dydx']
        p_borrow_usdc = stgy_instance.target_prices['borrow_usdc']
        p_add_collateral_dydx = stgy_instance.target_prices['add_collateral_dydx']
        p_close_short = stgy_instance.target_prices['close_short']
        p_open_short = stgy_instance.target_prices['open_short']
        floor = min(list(stgy_instance.target_prices.values()))
        p_repay_aave = stgy_instance.target_prices['repay_aave']
        p_ltv_limit = stgy_instance.target_prices['ltv_limit']
        axs.axhline(y=p_rtrn_usdc_n_rmv_coll_dydx, color='black', linestyle='--',
                    label='rtrn_usdc_n_rmv_coll_dydx')
        axs.axhline(y=p_borrow_usdc, color='darkgoldenrod', linestyle='--', label='borrow_usdc')
        axs.axhline(y=p_add_collateral_dydx, color='tab:orange', linestyle='--', label='add_collateral_dydx')
        axs.axhline(y=p_close_short, color='olive', linestyle='--', label='close_short')
        axs.axhline(y=p_open_short, color='darkred', linestyle='--', label='open_short')
        axs.axhline(y=floor, color='red', linestyle='--', label='floor')
        axs.axhline(y=p_repay_aave, color='magenta', linestyle='--', label='repay_aave')
        axs.axhline(y=p_ltv_limit, color='purple', linestyle='--', label='ltv_limit')
        print(p_ltv_limit, p_repay_aave)
        axs.grid()
        axs.legend(loc='lower left')
        plt.show()

    @staticmethod
    def plot_price_distribution(stgy_instance):
        # fig, axs = plt.subplots(1, 1, figsize=(21, 7))
        # from https://stackoverflow.com/questions/6855710/how-to-have-logarithmic-bins-in-a-python-histogram
        data = np.log(stgy_instance.historical_data['close'])
        MIN, MAX = data.min(), data.max()
        data.hist(bins=np.linspace(MIN, MAX, 50))
        plt.gca().set_xscale("log")
        plt.show()
        # print(np.log(historical_data['close']))

    @staticmethod
    def plot_returns_distribution(stgy_instance):
        """
        We assume returns are normally distributed
        """
        historical = stgy_instance.historical_data.copy()
        returns = historical['close'].pct_change().fillna(method='bfill')
        historical['returns'] = returns
        x = np.linspace(returns.min(), 1, 100)
        mean = np.mean(returns)
        std = np.std(returns)
        norm_dist = norm.pdf(x, mean, std)
        fig, axs = plt.subplots(1, 1, figsize=(21, 7))
        # returns.hist(bins=50, ax=axs)
        # axs.set_xlabel('Return')
        # axs.set_ylabel('Sample')
        # axs.set_title('Return distribution')
        # axs.plot(x, norm_dist, color='tab:blue', label='Returns dist')

        # To check if its normally distributed + understate the likelihood of returns beyond -2/+2 quantiles
        import scipy.stats as stats
        stats.probplot(historical['returns'], dist='norm', plot=axs)
        # axs.grid()
        plt.show()
        # print(historical.describe())

    @staticmethod
    def prob_return_in_range(stgy_instance, range):
        """
        range = [a, b] with a < b
        Recall:
        cumulative distribution function of a random variable X is F_X(x) := P(X <= x)
        So the probability of returns (R) falling in range is P(a <= R <= b) = P(R <= b) - P(R < a) = F_R(b) - F_R(a)
        If we assume returns are normally distributed then F could be estimated using norm(mean, std).cdf function
        """
        returns = stgy_instance.historical_data['returns']
        mean = np.mean(returns)
        std = np.std(returns)
        norm_cdf = norm(mean, std).cdf
        return norm_cdf(range[1]) - norm_cdf(range[0])
