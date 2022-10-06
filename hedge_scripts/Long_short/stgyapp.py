from hedge_scripts.Short_only.aave import Aave
from hedge_scripts.Short_only.dydx import Dydx
from hedge_scripts.Short_only.parameter_manager import ParameterManager
from hedge_scripts.Short_only.data_dumper import DataDamperNPlotter

class StgyApp(object):

    def __init__(self, config):

        self.stk = config["stk"]
        self.total_costs_from_aave_n_dydx = 0
        self.total_pnl = 0
        self.gas_fees = 0

        # prices and intervals
        self.trigger_prices = {}
        self.intervals = {}

        # clients for data
        # self.binance_client = binance_client_.BinanceClient(config["binance_client"])
        # self.dydx_client = dydx_client.DydxClient(config["dydx_client"])
        # self.sm_interactor = sm_interactor.SmInteractor(config["sm_interactor"])
        # self.historical_data =

        # We create attributes to fill later
        self.aave = None
        self.aave_features = None
        self.aave_rates = None

        self.dydx = None
        self.dydx_features = None

        # self.volatility_calculator = None

        self.parameter_manager = ParameterManager()

        self.historical_data = None


        self.data_dumper = DataDamperNPlotter()

    def launch(self, config):
        # self.call_binance_data_loader()
        self.initialize_aave(config['initial_parameters']['aave'])
        self.initialize_dydx(config['initial_parameters']['dydx'])

    # call clients functions
    def get_historical_data(self, symbol, freq,
                                 initial_date, save):
        eth_historical = self.binance_client.get_all_binance(symbol=symbol, freq=freq,
                                                             initial_date=initial_date, save=save)
        # self.historical_data = eth_historical
        self.historical_data = eth_historical["close"]
        for i in range(len(self.historical_data)):
            self.historical_data[i] = float(self.historical_data[i])
        # self.load_intervals()

    # initialize classes
    def initialize_aave(self, config):
        # We initialize aave and dydx classes instances
        self.aave = Aave(config)
        # We load methods and attributes for aave and dydx to use later
        self.aave_features = {"methods": [func for func in dir(self.aave)
                                          if (callable(getattr(self.aave, func))) & (not func.startswith('__'))],
                              "attributes": {"values": list(self.aave.__dict__.values()),
                                             "keys": list(self.aave.__dict__.keys())}}
        # We create an attribute for historical data
        self.aave_historical_data = []

    def initialize_dydx(self, config):
        self.dydx = Dydx(config)
        self.dydx_features = {"methods": [func for func in dir(self.dydx)
                                          if (callable(getattr(self.dydx, func))) & (not func.startswith('__'))],
                              "attributes": {"values": list(self.dydx.__dict__.values()),
                                             "keys": list(self.dydx.__dict__.keys())}}
        self.dydx_historical_data = []