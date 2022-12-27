import pandas as pd
import requests
import asyncio
import datetime
from tardis_client import TardisClient, Channel
from tardis_dev import datasets, get_exchange_details
from pprint import pprint


class Deribit(object):
    url = "https://test.deribit.com/api/v2/public/"

    def get_instruments(self):
        url = self.url + "get_instruments"
        resp = requests.get(url, params={'kind': 'option', 'currency': 'BTC'})
        result = resp.json()['result']
        instrument_names = []
        for data in result:
            instrument_name = data['instrument_name']
            if 'P' not in instrument_name:
                instrument_names.append(instrument_name)

        print(instrument_names)
        return instrument_names

    def get_order_book(self, instrument_names):
        url = self.url + "get_order_book"
        order_books = []
        for i, instrument_name in enumerate(instrument_names):
            order_books.append(requests.get(url, params={'instrument_name': instrument_name}).json()['result'])
            # if i == 5:
            #     break
        pprint(order_books)
        return order_books

    def create_csv(self, order_books):
        for order_book in order_books:
            df_bids = pd.DataFrame(
                data=order_book['bids'],
                columns=['price',
                         'amount']
            )

            df_asks = pd.DataFrame(
                data=order_book['asks'],
                columns=['price',
                         'amount']
            )

            df_bids.to_csv('/Users/akhileshgoswami/Desktop/HedgingScripts/BTC_Derbit_bids.csv', mode='a', header=False)
            df_asks.to_csv('/Users/akhileshgoswami/Desktop/HedgingScripts/BTC_Derbit_asks.csv', mode='a', header=False)

    def deribit_hist(self):
        # # pip install tardis-client
        # import asyncio
        # from tardis_client import TardisClient, Channel
        # tardis_client = TardisClient(api_key="YOUR_API_KEY")
        #
        # async def replay():
        #     # replay method returns Async Generator
        #     messages = tardis_client.replay(
        #         exchange="deribit",
        #         from_date="2019-07-01",
        #         to_date="2019-07-02",
        #         filters=[Channel(name="book", symbols=["OPTIONS"])]
        #     )
        #
        #     # messages as provided by Deribit real-time stream
        #     async for local_timestamp, message in messages:
        #         print(message)
        #
        # asyncio.run(replay())

        # pip install tardis-client
        # import asyncio
        # from tardis_client import TardisClient, Channel
        # tardis_client = TardisClient(api_key="YOUR_API_KEY")
        #
        # async def replay():
        #     # replay method returns Async Generator
        #     messages = tardis_client.replay(
        #         exchange="okex-options",
        #         from_date="2020-02-01",
        #         to_date="2020-02-02",
        #         filters=[Channel(name="option/trade", symbols=[])]
        #     )
        #
        #     # messages as provided by OKEx real-time stream
        #     async for local_timestamp, message in messages:
        #         print(message)
        #
        # asyncio.run(replay())

        # requires Python >=3.6
        # pip install tardis-dev

        import logging

        # optionally enable debug logs
        # logging.basicConfig(level=logging.DEBUG)

        exchange = 'deribit'
        exchange_details = get_exchange_details(exchange)

        # iterate over and download all data for every symbol
        for symbol in exchange_details["datasets"]["symbols"]:
            # alternatively specify datatypes explicitly ['trades', 'incremental_book_L2', 'quotes'] etc
            # see available options https://docs.tardis.dev/downloadable-csv-files#data-types
            data_types = symbol["dataTypes"]
            data_types = ['incremental_book_L2', 'book_snapshot_5', 'options_chain']

            symbol_id = symbol["id"]
            from_date = symbol["availableSince"]
            to_date = symbol["availableTo"]
            symbol_type = symbol['type']
            print(symbol)

            if 'option' not in symbol_type:
                continue

            if symbol_id in ['PERPETUALS', 'SPOT', 'FUTURES']:
                continue

            if '2022' not in from_date:
                continue

            if from_date < '2022-08-26T00:00:00.000Z':
                continue

            print(f"Downloading {exchange} {data_types} for {symbol_id} from {from_date} to {to_date}")
            # print('symbol:: ', symbol_id, from_date, to_date)

            # each CSV dataset format is documented at https://docs.tardis.dev/downloadable-csv-files#data-types
            # see https://docs.tardis.dev/downloadable-csv-files#download-via-client-libraries for full options docs
            datasets.download(
                exchange=exchange,
                data_types=data_types,
                from_date=from_date,
                to_date=to_date,
                symbols=[symbol_id],
                # TODO set your API key here
                api_key="TD.qu8XwTgCD2yrT2hC.G9za4OJj4UNPCUp.oU6MX-8YFSKsaLY.i5tiLA6IR9iUTZJ.PThJU5B4TUyCuvk.47-x",
                # path where CSV data will be downloaded into
                download_dir="./datasets",
            )

    def format_data(self):
        order_book = pd.read_csv('datasets/deribit_incremental_book_L2_2022-08-28_OPTIONS.csv')

        strike_prices = []
        expiry_date = []
        order_type = []
        open_at = []
        symbol_dict = {}
        for index, row in order_book.iterrows():
            if not row['symbol'] in symbol_dict:
                symbol_dict[row['symbol']] = []
            symbol_dict[row['symbol']].append(row)

        df = pd.DataFrame()

        data = []
        for key, value in symbol_dict.items():
            data.append(pd.DataFrame(value))

        df = pd.concat(data)
        for index, row in df.iterrows():
            symbol = row['symbol'].split('-')

            expiry_date.append(symbol[1])
            strike_prices.append(symbol[2])
            order_type.append(symbol[3])
            timestamp = int(row['timestamp']) / 1000

            format_date = datetime.datetime.utcfromtimestamp(timestamp / 1000).strftime('%c')
            date_time = format_date.split(' ')
            option_open_date = date_time[2]
            option_open_date += date_time[1]
            option_open_date += date_time[4][2] + date_time[4][3]
            open_at.append(option_open_date.upper())

        if 'Unnamed: 0' in df.columns:
            df.drop('Unnamed: 0', inplace=True, axis=1)
        df['strike'] = strike_prices
        df['written'] = open_at
        df['expiry'] = expiry_date
        df['type'] = order_type
        df.to_csv('datasets/deribit_incremental_book_L2_2022-08-28_OPTIONS.csv')


if __name__ == '__main__':
    d = Deribit()
    # instruments = d.get_instruments()
    # order_books = d.get_order_book(instruments)
    # d.create_csv(order_books)

    d.deribit_hist()
    # d.format_data()
    # d.drop_column()
