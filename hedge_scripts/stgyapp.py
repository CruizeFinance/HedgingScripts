import math
import json
import csv
# import pandas as pd
# import matplotlib
import pandas as pd
import pygsheets

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
        self.target_prices = dict(zip(target_prices_values,
                                      target_prices_names))
        self.intervals = {"infty": interval.Interval(target_prices_values[0],
                                                     math.inf,
                                                     "infty", 0),
                          "minus_infty": interval.Interval(-math.inf,
                                                           target_prices_values[-1],
                                                           "minus_infty", len(target_prices_values))
                          }
        for i in range(len(target_prices_values)-1):
            self.intervals[target_prices_names[i]] = interval.Interval(target_prices_values[i+1],
                                                                         target_prices_values[i],
                                                                         target_prices_names[i], i+1)



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

    def run_simulations(self):
        interval_old = self.intervals["infty"]
        for i in range(1, len(self.historical_data["close"]) - 1):
            new_interval_previous = self.historical_data["interval"][i - 1]
            new_interval_current = self.historical_data["interval"][i]
            new_market_price = self.historical_data["close"][i]
            # We could pass the whole AAVE_historical_df, DyDx_historical_df as parameters for scenarios if necessary
            self.find_scenario(new_market_price, new_interval_current, interval_old)
            if new_interval_previous != new_interval_current:
                interval_old = new_interval_previous

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
                              # "attributes": [[name, value] for name, value
                              #                in zip(list(self.aave.__dict__.keys()),
                              #                       list(self.aave.__dict__.values()))]}
        # We create an attribute for historical data
        self.aave_historical_data = []

    def initialize_dydx(self, config):
        self.dydx = dydx.Dydx(config)
        self.dydx_features = {"methods": [func for func in dir(self.dydx)
                                          if (callable(getattr(self.dydx, func))) & (not func.startswith('__'))],
                              "attributes": {"values": list(self.dydx.__dict__.values()),
                                             "keys": list(self.dydx.__dict__.keys())}}
                              # "attributes": [[name, value] for name, value
                              #                in zip(list(self.dydx.__dict__.keys()),
                              #                       list(self.dydx.__dict__.values()))]}
        self.dydx_historical_data = []

    # auxiliary functions
    def find_scenario(self, new_market_price, new_interval_current, interval_old):
        actions = self.actions_to_take(new_interval_current, interval_old)
        for action in actions:
            if action in self.aave_features["methods"]:
                if action == "borrow_usdc":
                    self.aave.borrow_usdc(new_market_price, new_interval_current, self.intervals)
                elif action == "repay_aave":
                    self.aave.repay_aave(new_market_price, new_interval_current, self.dydx, self.dydx_client)
                else:
                    getattr(self.aave, action)(new_market_price, new_interval_current, self.dydx)
            elif action in self.dydx_features["methods"]:
                if action == "add_collateral_dydx":
                    self.dydx.add_collateral_dydx(new_market_price, new_interval_current, self.aave)
                elif action == "open_short":
                    self.dydx.open_short(new_market_price, new_interval_current, self.aave, self.dydx_client)
                else:
                    getattr(self.dydx, action)(new_market_price, new_interval_current, self.aave)
        self.aave_historical_data.append(list(self.aave.__dict__.values()))
        self.dydx_historical_data.append(list(self.dydx.__dict__.values()))
        # print(list(self.aave.__dict__.values()), list(self.dydx.__dict__.values()))
        self.write_data()

    def write_data(self):
        # ESCRIBIMOS EL SHEET
        gc = pygsheets.authorize(service_file=
                                 '/home/agustin/Git-Repos/HedgingScripts/files/stgy-1-simulations-e0ee0453ddf8.json')
        sh = gc.open('aave/dydx simulations')
        data_aave = [str(i) for i in list(self.aave.__dict__.values())]
        data_dydx = [str(i) for i in list(self.dydx.__dict__.values())]
        sh[0].append_table(data_aave, end=None, dimension='ROWS', overwrite=False)
        sh[1].append_table(data_dydx, end=None, dimension='ROWS', overwrite=False)
        # open the file in the write mode
        # with open('/home/agustin/Escritorio/Empresas/Cruize Finance/Tasks/Estrategias/STGY 1/csv simulations/aave_csv.csv',
        #           'a') as f:
        #     # create the csv writer
        #     writer = csv.writer(f)
        #     # write a row to the csv file
        #     writer.writerow(list(self.aave.__dict__.values()))
        #     f.write("\n")
        # with open('/home/agustin/Escritorio/Empresas/Cruize Finance/Tasks/Estrategias/STGY 1/csv simulations/dydx_csv.csv',
        #           'w') as f:
        #     # create the csv writer
        #     writer = csv.writer(f, lineterminator="\n")
        #     # write a row to the csv file
        #     writer.writerow(list(self.dydx.__dict__.values()))

    def actions_to_take(self, new_interval_current, interval_old):
        actions = []
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):
                actions.append(list(self.intervals.keys())[i].replace("I_", ""))
        return actions

    def historical_parameters_data(self):
        aave_df = pd.DataFrame(self.aave_historical_data, columns=list(self.aave.__dict__.keys()))
        dydx_df = pd.DataFrame(self.dydx_historical_data, columns=list(self.dydx.__dict__.keys()))
        return {"aave_df": aave_df,
                "dydx_df": dydx_df}

if __name__ == "__main__":
    with open("/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json") as json_file:
        config = json.load(json_file)
    # aave.Aave(config["initial_parameters"]["aave"])
    # Initialize stgyApp
    stgy = StgyApp(config)

    # Load historical data
    stgy.call_binance_data_loader()
    # Assign intervals in which every price falls
    stgy.load_intervals()
    
    # Change initial_parameters to reflect first market price
    # We start at the 1-st element bc we will take the 0-th element as interval_old
    config["initial_parameters"]["aave"]["market_price"] = stgy.historical_data['close'][1]
    config["initial_parameters"]["aave"]["interval_current"] = stgy.historical_data['interval'][1]
    config["initial_parameters"]["aave"]["collateral"] = stgy.stk
    config["initial_parameters"]["dydx"]["market_price"] = stgy.historical_data['close'][1]
    config["initial_parameters"]["dydx"]["interval_current"] = stgy.historical_data['interval'][1]
    # print(config)
    stgy.launch(config)
    # print(stgy.dydx_features)
    interval_old = stgy.historical_data["interval"][0]
    # stgy.historical_parameters_data()
    # print(stgy.aave_df, stgy.dydx_df)
    for i in range(2, len(stgy.historical_data["close"])):
        new_interval_previous = stgy.historical_data["interval"][i - 1]
        new_interval_current = stgy.historical_data["interval"][i]
        new_market_price = stgy.historical_data["close"][i]
        # print(new_interval_current, interval_old)
        stgy.find_scenario(new_market_price, new_interval_current, interval_old)
        if new_interval_previous != new_interval_current:
            interval_old = new_interval_previous
        # partial_aave = pd.DataFrame(stgy.aave_features["attributes"]["values"],
        #                             columns=stgy.aave_features["attributes"]["keys"])
        # partial_dydx = pd.DataFrame(stgy.dydx_features["attributes"]["values"],
        #                             columns=stgy.dydx_features["attributes"]["keys"])

        print(stgy.historical_parameters_data()["aave_df"], stgy.historical_parameters_data()["dydx_df"])
# ######
# # run simulations
# interval_old = stgy.intervals["infty"]
# aave_parameters = config["initial_parameters"]["aave"]
# dydx_parameters = config["initial_parameters"]["dydx"]
# for i in range(1, len(summary["market_price"][i - 1]) - 1):
#     interval_previous = summary["price_in_interval"][i - 1]
#     # P_previous = P[i-1]
#     interval_current = summary["price_in_interval"][i]
#     market_price = summary["market_price"][i]
#     # We could pass the whole AAVE_historical_df, DyDx_historical_df as parameters for scenarios if necessary
#     stgy.find_scenario(market_price, interval_current, interval_old)
#     if interval_previous != interval_current:
#         interval_old = interval_previous

####################################
# aux
# self.p_floor = 1140
# self.p_return_USDC = 1250
# self.p_borrow_USDC = 1200
# self.p_remove_collateral_dydx = 1190
# self.p_add_collateral_dydx = 1180
# self.p_put_limit_order = 1170
# self.p_floor_threshold = 1160
# self.p_close_short = 1150

# interval_infty = interval.Interval(self.target_prices["return_USDC"], math.inf,
#                                    "I_infty", 0)
# interval_close_aave = interval.Interval(self.target_prices["borrow_USDC"], self.target_prices["return_USDC"],
#                                         "I_return_USDC", 1)
# interval_add_coll_aave = interval.Interval(self.target_prices["remove_collateral_dydx"], self.target_prices["borrow_USDC"],
#                                            "I_borrow_USDC", 2)
# interval_remove_coll_dydx = interval.Interval(self.target_prices["add_collateral_dydx"], self.target_prices["remove_collateral_dydx"],
#                                               "I_remove_collateral_dydx", 3)
# interval_add_coll_dydx = interval.Interval(self.target_prices["put_limit_order"], self.target_prices["add_collateral_dydx"],
#                                            "I_add_collateral_dydx", 4)
# interval_put_limit_order = interval.Interval(self.target_prices["close_short"], self.target_prices["put_limit_order"],
#                                              "I_put_limit_order", 5)
# interval_close_short = interval.Interval(self.target_prices["floor_threshold"], self.target_prices["close_short"],
#                                          "I_close_short", 6)
# interval_open_short = interval.Interval(self.target_prices["floor"], self.target_prices["floor_threshold"],
#                                         "I_open_short", 7)
# interval_minus_infty = interval.Interval(-math.inf, self.target_prices["floor"],
#                                          "I_minus_infty", 8)
# interval_aave_LTV_limit = interval.Interval(float("nan"),float("nan"),"I_"


# self.intervals = {interval_infty.name: interval_infty,
#                   interval_close_aave.name: interval_close_aave,
#                   interval_add_coll_aave.name: interval_add_coll_aave,
#                   interval_remove_coll_dydx.name: interval_remove_coll_dydx,
#                   interval_add_coll_dydx.name: interval_add_coll_dydx,
#                   interval_put_limit_order.name: interval_put_limit_order,
#                   interval_close_short.name: interval_close_short,
#                   interval_open_short.name: interval_open_short,
#                   interval_minus_infty.name: interval_minus_infty}