import pandas as pd
import math
import os.path
from binance.client import Client as Client_binance
from datetime import timedelta, datetime
from dateutil import parser


class BinanceClient(object):

    def __init__(self,
                 config):
        self.binance_api_key = config['binance_api_key']
        self.binance_api_secret = config['binance_api_secret']
        # self.batch_size = config['batch_size']
        self.symbol = config['symbol']
        self.freq = config['freq']
        ### CONSTANTS
        self.binsizes = {"1m": 1, "5m": 5, "10m": 10, "15m": 15, "1h": 60, "6h": 360, "12h": 720, "1d": 1440}
        # batch_size = 750
        self.client = Client_binance(api_key=self.binance_api_key, api_secret=self.binance_api_secret)

        # initial_date = '1 Jan 2017'
        self.initial_date = config['initial_date']

    ### FUNCTIONS
    def minutes_of_new_data(self, data, source):
        global old
        global new
        if len(data) > 0:
            old = parser.parse(data["timestamp"].iloc[-1])
        elif source == "binance":
            old = datetime.strptime(self.initial_date, '%d %b %Y')
        if source == "binance":
            new = pd.to_datetime(self.client.get_klines(symbol=self.symbol, interval=self.freq)[-1][0], unit='ms')
        return old, new

    def get_all_binance(self, save = False):
        filename = '%s-%s-data.csv' % (self.symbol, self.freq)
        if os.path.isfile(filename):
            self.data_df = pd.read_csv(filename)
        else:
            self.data_df = pd.DataFrame()
        oldest_point, newest_point = self.minutes_of_new_data(self.data_df, source = "binance")
        delta_min = (newest_point - oldest_point).total_seconds()/60
        available_data = math.ceil(delta_min/self.binsizes[self.freq])
        if oldest_point == datetime.strptime(self.initial_date, '%d %b %Y'):
            print('Downloading all available %s data for %s. Be patient..!' % (self.freq, self.symbol))
        else:
            print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.'
                  % (delta_min, self.symbol, available_data, self.freq))
        klines = self.client.get_historical_klines(self.symbol, self.freq, oldest_point.strftime("%d %b %Y %H:%M:%S"), newest_point.strftime("%d %b %Y %H:%M:%S"))
        data = pd.DataFrame(klines, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        if len(self.data_df) > 0:
            temp_df = pd.DataFrame(data)
            self.data_df = self.data_df.append(temp_df)
        else:
            self.data_df = data
        self.data_df.set_index('timestamp', inplace=True)
        if save:
            self.data_df.to_csv(filename)
        print('All caught up..!')
        # return self.data_df