import math
import json
import pandas as pd
import pygsheets
import matplotlib.pyplot as plt
import random
import numpy as np

import aave
import dydx
import interval
import binance_client_
import dydx_client
import sm_interactor


class StgyApp(object):

    def __init__(self, config):
        # We define intervals from target prices
        target_prices_values = config["target_prices"]["values"]
        target_prices_names = config["target_prices"]["names"]
        self.stk = config["stk"]
        self.total_costs = 0
        self.gas_fees = 0
        self.target_prices = dict(zip(target_prices_names,
                                      target_prices_values))
        self.intervals = {"infty": interval.Interval(target_prices_values[0],
                                                     math.inf,
                                                     "infty", 0),
                          }
        for i in range(len(target_prices_values)-1):
            self.intervals[target_prices_names[i]] = interval.Interval(
                target_prices_values[i+1],
                target_prices_values[i],
                target_prices_names[i], i+1)
        self.intervals["minus_infty"] = interval.Interval(-math.inf,
                                                          target_prices_values[-1],
                                                          "minus_infty",
                                                          len(target_prices_values))



        # clients for data
        self.binance_client = binance_client_.BinanceClient(config["binance_client"])
        self.dydx_client = dydx_client.DydxClient(config["dydx_client"])
        self.sm_interactor = sm_interactor.SmInteractor(config["sm_interactor"])
        # self.historical_data =

        # We create attributes to fill later
        self.aave = None
        self.aave_features = None
        self.aave_historical_data = None
        self.aave_rates = None
        self.aave_df = None

        self.dydx = None
        self.dydx_features = None
        self.dydx_historical_data = None
        self.dydx_df = None

        self.historical_data = None

    def launch(self, config):
        # self.call_binance_data_loader()
        self.initialize_aave(config['initial_parameters']['aave'])
        self.initialize_dydx(config['initial_parameters']['dydx'])
        self.call_dydx_client()
        self.call_sm_interactor()

    # def run_simulations(self):
    #     interval_old = self.intervals["infty"]
    #     for i in range(1, len(self.historical_data["close"]) - 1):
    #         new_interval_previous = self.historical_data["interval"][i - 1]
    #         new_interval_current = self.historical_data["interval"][i]
    #         new_market_price = self.historical_data["close"][i]
    #         # We could pass the whole AAVE_historical_df, DyDx_historical_df as parameters for scenarios if necessary
    #         self.find_scenario(new_market_price, new_interval_current, interval_old)
    #         if new_interval_previous != new_interval_current:
    #             interval_old = new_interval_previous

    # call clients functions
    def call_binance_data_loader(self):
        eth_historical = self.binance_client.get_all_binance(save=True)
        eth_prices = eth_historical[-2000:]["close"]
        for i in range(len(eth_prices)):
            eth_prices[i] = float(eth_prices[i])
        self.historical_data = pd.DataFrame(eth_prices, index=eth_prices.index)

    def call_dydx_client(self):
        self.dydx_client.get_dydx_parameters(self.dydx)

    def call_sm_interactor(self):
        self.aave_rates = self.sm_interactor.get_rates()

    # function to assign interval_current to each market_price in historical data
    def load_intervals(self):
        self.historical_data["interval"] = [[0, 0]] * len(self.historical_data["close"])
        self.historical_data["interval_name"] = ['nan'] * len(self.historical_data["close"])
        for loc in range(len(self.historical_data["close"])):
            market_price = self.historical_data["close"][loc]
            for i in list(self.intervals.values()):
                if i.left_border < market_price <= i.right_border:
                    self.historical_data["interval"][loc] = i
                    self.historical_data["interval_name"][loc] = i.name

    # initialize functions
    def initialize_aave(self, config):
        # We initialize aave and dydx classes instances
        self.aave = aave.Aave(config)
        # We load methods and attributes for aave and dydx to use later
        self.aave_features = {"methods": [func for func in dir(self.aave)
                                          if (callable(getattr(self.aave, func))) & (not func.startswith('__'))],
                              "attributes": {"values": list(self.aave.__dict__.values()),
                                             "keys": list(self.aave.__dict__.keys())}}
        # We create an attribute for historical data
        self.aave_historical_data = []

    def initialize_dydx(self, config):
        self.dydx = dydx.Dydx(config)
        self.dydx_features = {"methods": [func for func in dir(self.dydx)
                                          if (callable(getattr(self.dydx, func))) & (not func.startswith('__'))],
                              "attributes": {"values": list(self.dydx.__dict__.values()),
                                             "keys": list(self.dydx.__dict__.keys())}}
        self.dydx_historical_data = []

    # auxiliary functions
    def update_parameters(self, new_market_price, new_interval_current):
        # AAVE
        self.aave.market_price = new_market_price
        self.aave.interval_current = new_interval_current
        # Before updating collateral and debt we have to calculate last earned fees + update interests earned until now
        # As we are using hourly data we have to convert anual rate interest into hourly interest, therefore freq=365*24
        self.aave.lending_fees_calc(freq=365*24)
        self.aave.borrowing_fees_calc(freq=365*24)
        # We have to execute track_ first because we need the fees for current collateral and debt values
        self.aave.track_lend_borrow_interest()
        self.aave.update_debt() # we add the last borrowing fees to the debt
        self.aave.update_collateral() # we add the last lending fees to the collateral and update both eth and usd values
        self.aave.ltv = self.aave.ltv_calc()

        # DYDX
        self.dydx.market_price = new_market_price
        self.dydx.interval_current = new_interval_current
        self.dydx.notional = self.dydx.notional_calc()
        self.dydx.equity = self.dydx.equity_calc()
        self.dydx.leverage = self.dydx.leverage_calc()
        self.dydx.pnl = self.dydx.pnl_calc()
        self.dydx.price_to_liquidation = self.dydx.price_to_liquidation_calc(self.dydx_client)

    def find_scenario(self, new_market_price, new_interval_current, interval_old):
        actions = self.actions_to_take(new_interval_current, interval_old)
        self.simulate_fees()
        # We reset the costs in order to always start in 0
        self.aave.costs = 0
        self.dydx.costs = 0
        # aave_total_costs = []
        # dydx_total_costs = []
        for action in actions:
            if action in self.aave_features["methods"]:
                if action == "return_usdc":
                    self.aave.return_usdc(new_market_price, new_interval_current, self.gas_fees)
                elif action == "borrow_usdc":
                    self.aave.borrow_usdc(new_market_price, new_interval_current, self.gas_fees, self.intervals)
                elif (action == "repay_aave") | (action == "ltv_limit"):
                    self.aave.repay_aave(new_market_price, new_interval_current,
                                         self.gas_fees,
                                         self.dydx, self.dydx_client)
            elif action in self.dydx_features["methods"]:
                if action == "add_collateral_dydx":
                    self.dydx.add_collateral_dydx(new_market_price, new_interval_current,
                                                  self.gas_fees,
                                                  self.aave)
                elif action == "open_short":
                    self.dydx.open_short(new_market_price, new_interval_current,
                                         self.aave, self.dydx_client, self.intervals)
                else:
                    getattr(self.dydx, action)(new_market_price, new_interval_current)


            # For every action executed we add its associated costs
            # aave_total_costs.append(self.aave.costs)
            # dydx_total_costs.append(self.dydx.costs)
        # Now we sum up all the costs associated to all the executed actions
        # self.aave.costs = sum(aave_total_costs)
        # self.dydx.costs = sum(dydx_total_costs)
        # self.total_costs = self.total_costs + self.aave.costs + self.dydx.costs
        # self.aave_historical_data.append(list(self.aave.__dict__.values()))
        # self.dydx_historical_data.append(list(self.dydx.__dict__.values()))
        # # print(list(self.aave.__dict__.values()), list(self.dydx.__dict__.values()))
        # self.write_data()

    def actions_to_take(self, new_interval_current, interval_old):
        actions = []
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):
                actions.append(list(self.intervals.keys())[i])
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):
                actions.append(list(self.intervals.keys())[i])
        return actions

    def simulate_fees(self):
        self.gas_fees = random.choice(list(np.arange(1, 9, 0.5)))

    def add_costs(self):
        self.total_costs = self.total_costs + self.aave.costs + self.dydx.costs

    def write_data(self, new_interval_previous, interval_old, mkt_price_index):
        # ESCRIBIMOS EL SHEET
        gc = pygsheets.authorize(service_file=
                                 '/home/agustin/Git-Repos/HedgingScripts/files/stgy-1-simulations-e0ee0453ddf8.json')
        sh = gc.open('aave/dydx simulations')
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

        for i in range(len(self.aave.__dict__.values())):
            if list(self.aave.__dict__.keys())[i] in aave_wanted_keys:
                # print(list(self.aave.__dict__.keys())[i])
                if isinstance(list(self.aave.__dict__.values())[i], interval.Interval):
                    data_aave.append(str(list(self.aave.__dict__.values())[i].name))
                    data_aave.append(new_interval_previous.name)
                    data_aave.append(interval_old.name)
                else:
                    data_aave.append(str(list(self.aave.__dict__.values())[i]))
        for i in range(len(self.dydx.__dict__.values())):
            if isinstance(list(self.dydx.__dict__.values())[i], interval.Interval):
                data_dydx.append(str(list(self.dydx.__dict__.values())[i].name))
                data_dydx.append(new_interval_previous.name)
                data_dydx.append(interval_old.name)
            else:
                data_dydx.append(str(list(self.dydx.__dict__.values())[i]))
        # We add the index number of the appareance of market price in historical_data.csv order to find useful test values quicker
        data_aave.append(self.gas_fees)
        data_aave.append(self.total_costs)
        data_aave.append(mkt_price_index)
        data_dydx.append(self.gas_fees)
        data_dydx.append(self.total_costs)
        data_dydx.append(mkt_price_index)
        # print(data_aave, list(self.dydx.__dict__.keys()))
        sh[0].append_table(data_aave, end=None, dimension='ROWS', overwrite=False)
        sh[1].append_table(data_dydx, end=None, dimension='ROWS', overwrite=False)

    def historical_parameters_data(self):
        aave_df = pd.DataFrame(self.aave_historical_data, columns=list(self.aave.__dict__.keys()))
        dydx_df = pd.DataFrame(self.dydx_historical_data, columns=list(self.dydx.__dict__.keys()))
        return {"aave_df": aave_df,
                "dydx_df": dydx_df}

    def plot_data(self):
        fig, axs = plt.subplots(1, 1, figsize=(21, 7))
        axs.plot(self.historical_data['close'], color='tab:blue', label='market price')
        # axs.plot(list(pnl_), label='DyDx pnl')
        P_return_usdc = self.target_prices['return_usdc']
        P_borrow_usdc = self.target_prices['borrow_usdc']
        P_close_short = self.target_prices['close_short']
        P_open_short = self.target_prices['open_short']
        P_floor = min(list(self.target_prices.values()))
        axs.axhline(y=P_return_usdc, color='tab:orange', linestyle='--', label='return_usdc')
        axs.axhline(y=P_borrow_usdc, color='tab:orange', linestyle='--', label='borrow_usdc')
        axs.axhline(y=P_close_short, color='magenta', linestyle='--', label='close_short')
        axs.axhline(y=P_open_short, color='r', linestyle='--', label='open_short')
        axs.axhline(y=P_floor, color='r', linestyle='--', label='floor')
        axs.grid()
        axs.legend(loc='lower left')
        plt.show()



if __name__ == "__main__":
    with open("/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json") as json_file:
        config = json.load(json_file)
    # aave.Aave(config["initial_parameters"]["aave"])
    # Initialize stgyApp
    stgy = StgyApp(config)
    # Load historical data
    # stgy.call_binance_data_loader()
    # historical_data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1h-data.csv")
    # eth_prices = historical_data["close"]
    # for i in range(len(eth_prices)):
    #     eth_prices[i] = float(eth_prices[i])
    # stgy.historical_data = pd.DataFrame(eth_prices, index=eth_prices.index)
    stgy.historical_data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/stgy.historical_data.csv")
    # Assign intervals in which every price falls
    stgy.load_intervals()


    # print(historical_data)
    # Change initial_parameters to reflect first market price
    # We start at the 1-st element bc we will take the 0-th element as interval_old

    # From the stgy.historical_data we took a daterange in which several actions are executed
    initial_index = 3851 - 1
    final_index = 3922 - 1
    # print(config['stk'])
    stgy.launch(config)
    stgy.aave.market_price = stgy.historical_data['close'][initial_index]
    stgy.aave.interval_current = stgy.historical_data['interval'][initial_index]
    # stgy.aave.entry_price = 1681.06
    stgy.aave.collateral_eth = stgy.stk * 0.9
    stgy.aave.collateral_eth_initial = stgy.stk * 0.9
    stgy.reserve_margin_eth = stgy.stk * 0.1
    stgy.aave.collateral_usdc = stgy.aave.collateral_eth * stgy.aave.market_price
    stgy.reserve_margin_usdc = stgy.aave.reserve_margin_eth * stgy.aave.market_price
    # stgy.aave.usdc_status = True
    # stgy.aave.debt = 336.212
    # debt_initial
    # stgy.aave.price_to_ltv_limit = 672.424
    # stgy.total_costs = 104

    stgy.dydx.market_price = stgy.historical_data['close'][initial_index]
    stgy.dydx.interval_current = stgy.historical_data['interval'][initial_index]
    # stgy.dydx.collateral = stgy.aave.debt
    # stgy.dydx.equity = stgy.dydx.collateral
    # stgy.dydx.collateral_status = True
    #
    # price_floor = stgy.intervals['open_short'].left_border
    # previous_position_order = stgy.intervals['open_short'].position_order
    # stgy.intervals['floor'] = interval.Interval(stgy.aave.price_to_ltv_limit, price_floor,
    #                                        'floor', previous_position_order + 1)
    # stgy.intervals['minus_infty'] = interval.Interval(-math.inf, stgy.aave.price_to_ltv_limit,
    #                                              'minus_infty', previous_position_order + 2)

    interval_old = stgy.intervals['infty']

    for i in range(initial_index+1, final_index):
        new_interval_previous = stgy.historical_data["interval"][i-1]
        new_interval_current = stgy.historical_data["interval"][i]
        new_market_price = stgy.historical_data["close"][i]

        # We need to update interval_old BEFORE executing actions bc if not the algo could read the movement late
        # therefore not taking the actions needed as soon as they are needed
        if new_interval_previous != new_interval_current:
            interval_old = new_interval_previous

        # First we update everything in order to execute scenarios with updated values
        stgy.update_parameters(new_market_price, new_interval_current)
        stgy.find_scenario(new_market_price, new_interval_current, interval_old)
        # We are using hourly data so we add funding rates every 8hs (every 8 new prices)
        # Moreover, we need to call this method after find_scenarios in order to have all costs updated.
        # Calling it before find_scenarios will overwrite the funding by 0
        if (i - initial_index) % 8 == 0:
            stgy.dydx.add_funding_rates()
            # stgy.total_costs = stgy.total_costs + stgy.dydx.funding_rates

        stgy.add_costs()

        # We write the data into the google sheet
        stgy.write_data(new_interval_previous, interval_old, i)
    stgy.plot_data()
