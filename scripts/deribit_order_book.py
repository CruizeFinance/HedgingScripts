import pandas as pd
import requests
import asyncio
from tardis_client import TardisClient, Channel
from tardis_dev import datasets, get_exchange_details


class Deribit(object):
    url = "https://test.deribit.com/api/v2/public/"

    def get_order_book(self):
        url = self.url + "get_order_book"
        resp = requests.get(url, params={'depth': 50, 'instrument_name': 'ETH-26JUL19'})
        print(resp.json())
        return resp.json()['result']

    def create_csv(self, data):
        df_bids = pd.DataFrame(
            data=data['bids'],
            columns=['price',
                     'amount']
        )

        df_asks = pd.DataFrame(
            data=data['asks'],
            columns=['price',
                     'amount']
        )

        df_bids.to_csv('/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/scripts/Derbit_bids.csv')
        df_asks.to_csv(
            '/Users/prithvirajmurthy/Desktop/blockchain/cruize/scripts/scripts/Derbit_asks.csv')

    # def deribit_hist(self):
    #     # # pip install tardis-client
    #     # import asyncio
    #     # from tardis_client import TardisClient, Channel
    #     # tardis_client = TardisClient(api_key="YOUR_API_KEY")
    #     #
    #     # async def replay():
    #     #     # replay method returns Async Generator
    #     #     messages = tardis_client.replay(
    #     #         exchange="deribit",
    #     #         from_date="2019-07-01",
    #     #         to_date="2019-07-02",
    #     #         filters=[Channel(name="book", symbols=["OPTIONS"])]
    #     #     )
    #     #
    #     #     # messages as provided by Deribit real-time stream
    #     #     async for local_timestamp, message in messages:
    #     #         print(message)
    #     #
    #     # asyncio.run(replay())
    #
    #     # pip install tardis-client
    #     # import asyncio
    #     # from tardis_client import TardisClient, Channel
    #     # tardis_client = TardisClient(api_key="YOUR_API_KEY")
    #     #
    #     # async def replay():
    #     #     # replay method returns Async Generator
    #     #     messages = tardis_client.replay(
    #     #         exchange="okex-options",
    #     #         from_date="2020-02-01",
    #     #         to_date="2020-02-02",
    #     #         filters=[Channel(name="option/trade", symbols=[])]
    #     #     )
    #     #
    #     #     # messages as provided by OKEx real-time stream
    #     #     async for local_timestamp, message in messages:
    #     #         print(message)
    #     #
    #     # asyncio.run(replay())
    #
    #     # requires Python >=3.6
    #     # pip install tardis-dev
    #
    #     import logging
    #
    #     # optionally enable debug logs
    #     # logging.basicConfig(level=logging.DEBUG)
    #
    #     exchange = 'deribit'
    #     exchange_details = get_exchange_details(exchange)
    #
    #     # iterate over and download all data for every symbol
    #     for symbol in exchange_details["datasets"]["symbols"]:
    #         # alternatively specify datatypes explicitly ['trades', 'incremental_book_L2', 'quotes'] etc
    #         # see available options https://docs.tardis.dev/downloadable-csv-files#data-types
    #         data_types = symbol["dataTypes"]
    #         symbol_id = symbol["id"]
    #         from_date = symbol["availableSince"]
    #         to_date = symbol["availableTo"]
    #
    #         print('symbol:: ', symbol_id)
    #         # skip groupped symbols
    #         if symbol_id in ['PERPETUALS', 'SPOT', 'FUTURES']:
    #             continue
    #
    #         print(f"Downloading {exchange} {data_types} for {symbol_id} from {from_date} to {to_date}")
    #
    #         # each CSV dataset format is documented at https://docs.tardis.dev/downloadable-csv-files#data-types
    #         # see https://docs.tardis.dev/downloadable-csv-files#download-via-client-libraries for full options docs
    #         datasets.download(
    #             exchange=exchange,
    #             data_types=data_types,
    #             from_date=from_date,
    #             to_date=to_date,
    #             symbols=[symbol_id],
    #             # TODO set your API key here
    #             api_key="YOUR_API_KEY",
    #             # path where CSV data will be downloaded into
    #             download_dir="./datasets",
    #         )

if __name__ == '__main__':
    d = Deribit()
    order_book = d.get_order_book()
    d.create_csv(order_book)
    # d.deribit_hist()