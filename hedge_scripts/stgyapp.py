import json
import pandas as pd
import math

import aave
import dydx
import binance_client_
import dydx_client
import sm_interactor
import volatility_calculator
import data_dumper
import parameter_manager
import interval


class StgyApp(object):
    def __init__(self, config):

        self.stk = config["stk"]
        self.total_costs = 0
        self.gas_fees = 0

        # prices and intervals
        self.target_prices = {}
        self.intervals = {}

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

        self.volatility_calculator = None

        self.parameter_manager = parameter_manager.ParameterManager()

        self.historical_data = None

        self.data_dumper = data_dumper.DataDamperNPlotter()

    def launch(self, config):
        # self.call_binance_data_loader()
        self.initialize_aave(config["initial_parameters"]["aave"])
        self.initialize_dydx(config["initial_parameters"]["dydx"])
        self.call_dydx_client()
        self.call_sm_interactor()
        # self.initialize_volatility_calculator()
        # floor = 1300
        # self.define_target_prices(floor)
        # self.define_intervals()

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
    def call_binance_data_loader(self, symbol, freq, initial_date, save):
        eth_historical = self.binance_client.get_all_binance(
            symbol=symbol, freq=freq, initial_date=initial_date, save=save
        )
        # self.historical_data = eth_historical
        self.historical_data = eth_historical["close"]
        for i in range(len(self.historical_data)):
            self.historical_data[i] = float(self.historical_data[i])
        # self.load_intervals()

    def call_dydx_client(self):
        self.dydx_client.get_dydx_parameters(self.dydx)

    def call_sm_interactor(self):
        self.aave_rates = self.sm_interactor.get_rates()

    # initialize classes
    def initialize_aave(self, config):
        # We initialize aave and dydx classes instances
        self.aave = aave.Aave(config)
        # We load methods and attributes for aave and dydx to use later
        self.aave_features = {
            "methods": [
                func
                for func in dir(self.aave)
                if (callable(getattr(self.aave, func))) & (not func.startswith("__"))
            ],
            "attributes": {
                "values": list(self.aave.__dict__.values()),
                "keys": list(self.aave.__dict__.keys()),
            },
        }
        # We create an attribute for historical data
        self.aave_historical_data = []

    def initialize_dydx(self, config):
        self.dydx = dydx.Dydx(config)
        self.dydx_features = {
            "methods": [
                func
                for func in dir(self.dydx)
                if (callable(getattr(self.dydx, func))) & (not func.startswith("__"))
            ],
            "attributes": {
                "values": list(self.dydx.__dict__.values()),
                "keys": list(self.dydx.__dict__.keys()),
            },
        }
        self.dydx_historical_data = []

    def initialize_volatility_calculator(self):
        self.volatility_calculator = volatility_calculator.VolatilityCalculator()


if __name__ == "__main__":
    # load configurations
    with open(
        "/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json"
    ) as json_file:
        config = json.load(json_file)

    # Initialize stgyApp
    stgy = StgyApp(config)

    # Track historical data
    # symbol = 'ETHUSDC'
    # freq = '1m'
    # initial_date = "1 Jan 2019"
    # stgy.call_binance_data_loader(symbol=symbol, freq=freq,
    #                               initial_date=initial_date, save=True)

    # Load historical data if previously tracked and saved
    historical_data = pd.read_csv(
        "/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1m-data.csv"
    )[-30000:]
    # # assign data to stgy instance + define index as dates
    stgy.historical_data = pd.DataFrame(historical_data["close"], columns=["close"])
    timestamp = pd.to_datetime(historical_data["timestamp"])
    stgy.historical_data.index = timestamp
    #
    # #######################################################
    # # Simulations

    # Define floor
    floor = stgy.historical_data["close"].max() * 0.8
    #########################
    # Define trigger prices and thresholds
    N_week = 1 * 1 * 7 * 24 * 60  # 7 days
    data_for_thresholds = stgy.historical_data[:N_week].copy()  # First week of data
    stgy.parameter_manager.define_target_prices(
        stgy, N_week, data_for_thresholds, floor
    )
    stgy.parameter_manager.define_intervals(stgy)
    stgy.parameter_manager.load_intervals(stgy)
    #########################
    # Save historical data with trigger prices and thresholds loaded
    # stgy.historical_data.to_csv("/home/agustin/Git-Repos/HedgingScripts/files/stgy.historical_data.csv")
    #########################
    # Here we define initial parameters for AAVE and DyDx depending on at which price we are starting simulations

    # Define initial and final index if needed in order to only run simulations in periods of several trigger prices
    # As we calculate vol using first week of data, we initialize simulations from that week on
    initial_index = N_week + 1
    # final_index = 3923 - 1
    # print(config['stk'])
    stgy.launch(config)

    # AAVE
    stgy.aave.market_price = stgy.historical_data["close"][initial_index]
    stgy.aave.interval_current = stgy.historical_data["interval"][initial_index]
    stgy.aave.entry_price = stgy.target_prices["open_close"]
    stgy.aave.collateral_eth = round(stgy.stk * 0.9, 3)
    stgy.aave.collateral_eth_initial = round(stgy.stk * 0.9, 3)
    stgy.reserve_margin_eth = stgy.stk * 0.1
    stgy.aave.collateral_usdc = stgy.aave.collateral_eth * stgy.aave.market_price
    stgy.reserve_margin_usdc = stgy.aave.reserve_margin_eth * stgy.aave.market_price
    stgy.aave.usdc_status = True
    stgy.aave.debt = (
        stgy.aave.collateral_eth_initial
        * stgy.target_prices["open_close"]
        * stgy.aave.borrowed_percentage
    )
    # debt_initial
    stgy.aave.price_to_ltv_limit = round(
        stgy.aave.entry_price * stgy.aave.borrowed_percentage / 0.5, 3
    )
    # stgy.total_costs = 104

    # DyDx
    stgy.dydx.market_price = stgy.historical_data["close"][initial_index]
    stgy.dydx.interval_current = stgy.historical_data["interval"][initial_index]
    stgy.dydx.collateral = stgy.aave.debt
    stgy.dydx.equity = stgy.dydx.collateral
    stgy.dydx.collateral_status = True
    #########################
    # Change or define prices that aren't defined yet if the period of simulations involves those prices
    # For ex if we are executing periods of time in which ltv_limit or repay_aave are already defined

    # price_floor = stgy.intervals['open_close'].left_border
    previous_position_order = stgy.intervals["open_close"].position_order
    stgy.intervals["floor"] = interval.Interval(
        stgy.aave.price_to_ltv_limit, floor, "floor", previous_position_order + 1
    )
    stgy.intervals["minus_infty"] = interval.Interval(
        -math.inf,
        stgy.aave.price_to_ltv_limit,
        "minus_infty",
        previous_position_order + 2,
    )

    #########################
    # Load interval_old
    interval_old = stgy.intervals["infty"]
    #########################
    # Clear previous csv data for aave and dydx
    stgy.data_dumper.delete_results()
    #########################
    # add header to csv of aave and dydx
    stgy.data_dumper.add_header()
    #########################
    import time

    # run simulations
    starttime = time.time()
    print("starttime:", starttime)
    # for i in range(initial_index, len(stgy.historical_data)):
    i = initial_index
    while i < len(stgy.historical_data):
        # for i in range(initial_index, len(stgy.historical_data)):
        # pass
        new_interval_previous = stgy.historical_data["interval"][i - 1]
        new_interval_current = stgy.historical_data["interval"][i]
        new_market_price = stgy.historical_data["close"][i]
        #########################
        # We need to update interval_old BEFORE executing actions bc if not the algo could read the movement late
        # therefore not taking the actions needed as soon as they are needed
        if new_interval_previous != new_interval_current:
            interval_old = new_interval_previous
        #########################
        # Update parameters
        # First we update everything in order to execute scenarios with updated values
        stgy.parameter_manager.update_parameters(
            stgy, new_market_price, new_interval_current
        )
        time_used = stgy.parameter_manager.find_scenario(
            stgy, new_market_price, new_interval_current, interval_old, i
        )
        #########################
        # Funding rates
        # We are using hourly data so we add funding rates every 8hs (every 8 new prices)
        # Moreover, we need to call this method after find_scenarios in order to have all costs updated.
        # Calling it before find_scenarios will overwrite the funding by 0
        # We have to check all the indexes between old index i and next index i+time_used
        for index in range(i, i + time_used):
            if (index - initial_index) % (8 * 60) == 0:
                stgy.dydx.add_funding_rates()
                # stgy.total_costs = stgy.total_costs + stgy.dydx.funding_rates
        #########################
        # Add costs
        stgy.parameter_manager.add_costs(stgy)
        #########################
        # Write data
        # We write the data into the google sheet or csv file acording to sheet value
        # (sheet = True --> sheet, sheet = False --> csv)
        stgy.data_dumper.write_data(
            stgy, new_interval_previous, interval_old, i, sheet=False
        )
        #########################
        # Update trigger prices and thresholds
        # We update trigger prices and thresholds every day
        if (i + time_used - initial_index) % (1 * 24 * 60) == 0:
            # We call the paramater_manager instance with updated data
            data_for_thresholds = stgy.historical_data[:i].copy()
            stgy.parameter_manager.define_target_prices(
                stgy, N_week, data_for_thresholds, floor
            )
            stgy.parameter_manager.define_intervals(stgy)
            stgy.parameter_manager.load_intervals(stgy)
            save = True
            # stgy.data_dumper.plot_data(stgy)#, save, factors, vol, period)

        # we increment index by the time consumed in executing actions
        i += time_used

    endtime = time.time()
    print("endtime:", endtime)
