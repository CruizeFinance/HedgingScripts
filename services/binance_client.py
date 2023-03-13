# import math
# import multiprocessing
#
# import pandas as pd
# import os.path
# from datetime import timedelta, datetime
# from dateutil import parser
# from binance.client import Client as Client_binance
#
#
# class BinanceClient(object):
#     def __init__(self,
#                  config):
#         self.binance_api_key = config['binance_api_key']
#         self.binance_api_secret = config['binance_api_secret']
#         self.client = Client_binance(api_key=self.binance_api_key, api_secret=self.binance_api_secret)
#         # self.initial_date = config['initial_date']
#         # self.symbol = config['symbol']
#         # self.freq = config['freq']
#
#     ### FUNCTIONS
#     def minutes_of_new_data(self, symbol, kline_size,
#                             initial_date, data, source, end_date=0):
#         if len(data) > 0:
#             old = parser.parse(data["timestamp"].iloc[-1])
#         elif source == "binance":
#             old = datetime.strptime(initial_date, '%d %b %Y')
#         if source == "binance":
#             data = self.client.get_klines(symbol=symbol, interval=kline_size)
#             print('size: ', len(data))
#             new = pd.to_datetime(data[end_date][0], unit='ms')
#         return old, new
#
#     def get_all_binance(self, symbol, freq,
#                         initial_date, save=False, end_date=0):
#         binsizes = {"1m": 1, "5m": 5, "10m": 10, "15m": 15, "1h": 60, "6h": 360, "12h": 720, "1d": 1440}
#         filename = '/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/files/%s-%s-%s-data.csv' % (
#         symbol, freq, initial_date)
#         data_df = pd.DataFrame()
#         oldest_point, newest_point = self.minutes_of_new_data(symbol, freq,
#                                                               initial_date, data_df, source="binance", end_date=end_date)
#         delta_min = (newest_point - oldest_point).total_seconds() / 60
#         available_data = math.ceil(delta_min / binsizes[freq])
#         if oldest_point == datetime.strptime(initial_date, '%d %b %Y'):
#             print('Downloading all available %s data for %s. Be patient..!' % (freq, symbol))
#         else:
#             print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.'
#                   % (delta_min, symbol, available_data, freq))
#         klines = self.client.get_historical_klines(symbol, freq,
#                                                    oldest_point.strftime("%d %b %Y %H:%M:%S"),
#                                                    newest_point.strftime("%d %b %Y %H:%M:%S"))
#         data = pd.DataFrame(klines,
#                             columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
#                                      'quote_av',
#                                      'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
#         data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
#         # data.index = pd.to_datetime(data['timestamp'], unit='ms')
#         if len(data_df) > 0:
#             temp_df = pd.DataFrame(data)
#             data_df = data_df.append(temp_df)
#         else:
#             data_df = data
#         data_df.set_index('timestamp', inplace=True)
#         if save:
#             data_df.to_csv(filename)
#         print('All caught up..!')
#         print(initial_date)
#         return data_df
#
#
# if __name__ == '__main__':
#
#     import json
#     from joblib import Parallel, delayed
#
#     with open('/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/StgyApp_config.json') as json_file:
#         config = json.load(json_file)
#     _binance_client_ = BinanceClient(config['binance_client'])
#
#     symbol = 'ETHUSDC'
#     freq = '1m'
#     initial_dates = ["1 Jan 2022", "1 Jan 2021", "1 Jan 2020", "1 Jan 2019", "1 Jan 2018", "1 Jan 2017", "1 Jan 2016",
#                      "1 Jan 2015", "1 Jan 2014"]
#     end_dates = [-1, 232, 963, 1328, 1693, 2058, 2424, 2789, 3154]
#
#     # eth_historical_prices_year_wise = []
#     parallel_pool = Parallel(n_jobs=9)
#     delayed_function = [delayed(_binance_client_.get_all_binance)(symbol=symbol, freq=freq,
#                                                                   initial_date=initial_date, save=True,
#                                                                   end_date=end_date) for initial_date, end_date in
#                         zip(initial_dates, end_dates)]
#
#     eth_historical_prices_year_wise = parallel_pool(delayed_function)
#     print('eth_historical_prices_year_wise', eth_historical_prices_year_wise)
#
#     # eth_prices_float = []
#     # for i, eth_prices in enumerate(eth_historical_prices_year_wise):
#     #     eth_prices_float.append([])
#     #     for eth_price in eth_prices:
#     #         eth_prices_float[i].append(float(eth_price))
#     #
#     # historical_data = eth_prices_float
#     # print(historical_data)

import math
import pandas as pd
import os.path
from datetime import timedelta, datetime
from dateutil import parser
from binance.client import Client as Client_binance


class BinanceClient(object):

    def __init__(self,
                 config):
        self.binance_api_key = config['binance_api_key']
        self.binance_api_secret = config['binance_api_secret']

        self.client = Client_binance(api_key=self.binance_api_key, api_secret=self.binance_api_secret)

    ### FUNCTIONS
    def minutes_of_new_data(self, symbol, initial_date,
                            kline_size, data, source):
        if len(data) > 0:
            old = parser.parse(data["timestamp"].iloc[-1])
        elif source == "binance":
            old = datetime.strptime(initial_date, '%d %b %Y')
        if source == "binance":
            new = pd.to_datetime(self.client.get_klines(symbol=symbol, interval=kline_size)[-1][0], unit='ms')
        return old, new

    def get_all_binance(self, symbol, initial_date, freq, save=False):
        binsizes = {"1m": 1, "5m": 5, "10m": 10, "15m": 15, "1h": 60, "6h": 360, "12h": 720, "1d": 1440}
        filename = '/home/agustin/Git-Repos/algo-trading-crypto/il-hedger/il_hedger/files/%s-%s-data.csv' % (
            symbol, freq)
        if os.path.isfile(filename):
            data_df = pd.read_csv(filename)
        else:
            data_df = pd.DataFrame()
        oldest_point, newest_point = self.minutes_of_new_data(symbol, initial_date,
                                                              freq, data_df, source="binance")
        delta_min = (newest_point - oldest_point).total_seconds() / 60
        available_data = math.ceil(delta_min / binsizes[freq])
        if oldest_point == datetime.strptime(initial_date, '%d %b %Y'):
            print('Downloading all available %s data for %s. Be patient..!' % (freq, symbol))
        else:
            print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data.'
                  % (delta_min, symbol, available_data, freq))
        klines = self.client.get_historical_klines(symbol, freq,
                                                   oldest_point.strftime("%d %b %Y %H:%M:%S"),
                                                   newest_point.strftime("%d %b %Y %H:%M:%S"))
        data = pd.DataFrame(klines,
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                     'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        if len(data_df) > 0:
            temp_df = pd.DataFrame(data)
            data_df = data_df.append(temp_df)
        else:
            data_df = data
        data_df.set_index('timestamp', inplace=True)
        if save:
            data_df.to_csv(filename)
        print('All caught up..!')
        return data_df


if __name__ == '__main__':

    import json

    with open('/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/StgyApp_config.json') as json_file:
        config = json.load(json_file)
    _binance_client_ = BinanceClient(config['binance_client'])

    # Track historical data
    symbol_eth = 'ETHBUSD'
    symbol_btc = 'BTCBUSD'
    freq = '1d'
    initial_date = "1 Jan 2021"
    _binance_client_ = BinanceClient(config['binance_client'])
    eth_historical = _binance_client_.get_all_binance(symbol=symbol_eth, freq=freq,
                                                      initial_date=initial_date, save=False)
    btc_historical = _binance_client_.get_all_binance(symbol=symbol_btc, freq=freq,
                                                      initial_date=initial_date, save=False)
    eth_prices = eth_historical['close']
    for i in range(len(eth_prices)):
        print(eth_prices[i])
        eth_prices[i] = float(eth_prices[i])
    btc_prices = btc_historical['close']
    for i in range(len(btc_prices)):
        print()
        btc_prices[i] = float(btc_prices[i])
