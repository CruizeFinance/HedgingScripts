import json
import math
import numpy as np
from scipy.stats import norm
import pandas as pd

from stgyapp import StgyApp

def parametric_var(data, confidence, case):
    N_1y = 365 * 24 * 60
    N_6m = 180 * 24 * 60
    N_3m = 90 * 24 * 60
    if case == "lognormal returns":
        returns = pd.DataFrame(list(round(data.pct_change().dropna()['close']+1, 3)))[0]  # pct_change(1) = p_t+1 / p_t -1 = return - 1
        ewm_1y = returns[-N_1y:].ewm(alpha=0.8, adjust=False)
        ewm_6m = returns[-N_6m:].ewm(alpha=0.8, adjust=False)
        ewm_3m = returns[-N_3m:].ewm(alpha=0.8, adjust=False)
    elif case == "normal logreturns":
        log_returns = np.log(data['close']) - np.log(data['close'].shift(1))
        ewm_1y = log_returns[-N_1y:].ewm(alpha=0.8, adjust=False)
        ewm_6m = log_returns[-N_6m:].ewm(alpha=0.8, adjust=False)
        ewm_3m = log_returns[-N_3m:].ewm(alpha=0.8, adjust=False)
    else:
        print("Enter a valid case")
        return
    mean_1y = ewm_1y.mean().mean()
    std_1y = ewm_1y.std().mean()
    mean_6m = ewm_6m.mean().mean()
    std_6m = ewm_6m.std().mean()
    mean_3m = ewm_3m.mean().mean()
    std_3m = ewm_3m.std().mean()
    factor_add = round(norm.ppf(confidence), 3)
    # We use a weighted linea combination of 1y, 6m and 3m drift and vol
    # We convert it to 10m metrics as we are updating it every 10m
    if case == "lognormal returns":
        # In this case we need to take drift_T = (mu-sigma^2/2)*T, vol_T = sigma * sqrt(T)
        drift_10_weighted = ((mean_3m-std_3m**2/2) * 10) * 0.6 \
                               + ((mean_6m-std_6m**2/2) * 10) * 0.3 \
                               + ((mean_1y-std_1y**2/2) * 10) * 0.1
        vol_10_weighted = (std_3m * np.sqrt(10)) * 0.6 \
                                  + (std_6m * np.sqrt(10)) * 0.3 \
                                  + (std_1y * np.sqrt(10)) * 0.1
        return math.e ** (drift_10_weighted + factor_add * vol_10_weighted)
    elif case == "normal logreturns":
        drift_10_weighted = (mean_3m * 10) * 0.6 \
                         + (mean_6m * 10) * 0.3 \
                         + (mean_1y * 10) * 0.1
        vol_10_weighted = (std_3m * np.sqrt(10)) * 0.6 \
                       + (std_6m * np.sqrt(10)) * 0.3 \
                       + (std_1y * np.sqrt(10)) * 0.1
        return math.e ** (drift_10_weighted + factor_add * vol_10_weighted)

def historical_var(data, confidence, case):
    # This is just the X-percentil in the historical changes
    if case == "var of returns":
        returns = pd.DataFrame(list(data.pct_change(10).dropna()['close']+1))[0]  # pct_change(1) = p_t+1 / p_t -1 = return - 1
        changes_for_var = returns
    elif case == "var of log returns":
        log_returns = np.log(data['close']) - np.log(data['close'].shift(10))
        changes_for_var = log_returns
    else:
        print("Enter a valid case")
        return
    # difference_in_portf_value_pcg = []
    # for i in range(len(changes_for_var)):
    #     # if we use pct_change we should sum 1 in order to get returns
    #     difference_in_portf_value_pcg.append([changes_for_var[i], i])
    # difference_in_portf_value_pcg.sort()
    changes_for_var = changes_for_var.sort_values(ascending=True)
    changes_for_var.index = range(len(changes_for_var))
    index_for_var = int(len(changes_for_var) * confidence)
    return {'var': changes_for_var[index_for_var],
            'index_in_data_for_that_var': index_for_var}

def weighted_var(data, confidence, method, case):
    if method == "parametric":
        return parametric_var(data, confidence, case)
    elif method == "historical":
        var_3m = historical_var(data[-3 * 30 * 24 * 60:], confidence, case)['var']
        var_6m = historical_var(data[-6 * 30 * 24 * 60:], confidence, case)['var']
        var_1y = historical_var(data[-12 * 30 * 24 * 60:], confidence, case)['var']
        return 0.6 * var_3m + 0.3 * var_6m + 0.1 * var_1y

def run_through_dataset(data_set, historical_dataset):
    var_misses = {'total_misses': 0,
                  'index_of_miss': []}
    index_copy = list(data_set.index)
    data_set.index = range(len(data_set))
    var = weighted_var(data_set, 0.99, "historical", "var of returns")
    # var = weighted_var(data_set, 0.99, "parametric", "normal logreturns")
    i = 10
    # Let's count var misses while current price is above p_add_current
    new_p_add = p_open_close*var
    while data_set["close"][i] > new_p_add:
        print("current index: ", i)
        # print(var)
        print("var misses:", var_misses)
        current_price = data_set["close"][i]
        # last_10min_price = data_set["close"][i-10]
        next_10min_price = data_set["close"][i + 10]
        #########################
        # Count the number of times current 10min change was greater than current var
        if current_price/next_10min_price > var:
            print("curre price: ", current_price)
            print("next 10m price: ", next_10min_price)
            print("change:", current_price/next_10min_price)
            print("var:", var)
            print("difference: ", current_price / next_10min_price - var)
            var_misses['total_misses'] += 1
            var_misses['index_of_miss'].append(i)
        #########################
        N_1y = 12 * 30 * 24 * 60
        actual_current_data_set_index = index_copy[i]
        last_year_data = historical_dataset.loc[:actual_current_data_set_index][-N_1y:].copy()
        var = weighted_var(last_year_data, 0.99, "historical", "var of returns")
        # var = weighted_var(last_year_data, 0.99, "parametric", "normal logreturns")
        new_p_add = p_open_close*var
        i += 1
    return {"var misses": var_misses,
            "P_add when reached by P_current": new_p_add,
            "Index at which P_current reached P_add": i}

if __name__ == '__main__':
    data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1m-data_since_1 Sep 2019.csv")
    historical_data = pd.DataFrame(data["close"], columns=['close'])
    timestamp = pd.to_datetime(data['timestamp'])
    historical_data.index = timestamp

    # data for var check
    #
    data_for_var = historical_data[-3 * 30 * 24 * 60:]

    # Define floor. We set the floor to be 80% of the month of data previous to our data_for_var
    # We will update floor for every new price
    floor = 1100#historical_data[-4 * 30 * 24 * 60:-3 * 30 * 24 * 60]['close'].max() * 0.8
    p_open_close = floor * 1.01
    #######################
    # import matplotlib.pyplot as plt
    # var = weighted_var(data_for_var, 0.99, "parametric", "normal logreturns")
    # i = 10
    # # Let's count var misses while current price is above p_add_current
    # new_p_add = p_open_close * var
    # fig, axs = plt.subplots(1, 1, figsize=(21, 7))
    # # fig.suptitle("Factors = (%s, %s, %s), Vol=%s, Period=%s to %s" % (factors[0], factors[1], factors[2],
    # #                                                                   vol, period[0], period[1]))
    # axs.plot(historical_data[-4 * 30 * 24 * 60:], color='tab:blue', label='market price')
    # axs.axhline(y=floor, color='red', linestyle='--', label='floor')
    # axs.axhline(y=p_open_close, color='darkred', linestyle='--', label='open_close')
    # axs.axhline(y=new_p_add, color='darkred', linestyle='--', label='p_add')
    # # axs.plot(data_for_var.iloc[10]['close'])
    # axs.grid()
    # axs.legend(loc='lower left')
    # plt.show()
    #############
    # data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1m-data.csv")
    # historical_data = pd.DataFrame(data["close"], columns=['close'])
    # timestamp = pd.to_datetime(data['timestamp'])
    # historical_data.index = timestamp

    # data for var check
    # data_for_var = historical_data[-3 * 30 * 24 * 60:]
    # print(historical_var(data_for_var, 0.99, "var of returns"))
    # print(historical_var(data_for_var, 0.99, "Hull"))
    # print(parametric_var(data_for_var, 0.99))
    # print(data_for_var.pct_change().dropna()['close'][-1], data_for_var['close'][-1]/data_for_var['close'][-2]-1)

    var_misses = run_through_dataset(data_for_var,
                                     historical_data)["var misses"]
    print(var_misses)

    # Parallel execution. We divide out whole dataset into smaller datasets of 60000 prices (~ 41 days of data)
    # from joblib import Parallel, delayed
    # parallel_pool = Parallel(n_jobs=9)
    # delayed_function = [delayed(run_through_dataset)(
    #     data_set=stgy.historical_data[first_index+60000*i:first_index+60000*(i+1)],
    #     historical_dataset=stgy.historical_data)
    #     for i in range(9)]
    # var_misses_total = parallel_pool(delayed_function)
    # print('var_misses', var_misses_total)