from datetime import datetime

from decouple import config
from dydx3 import Client
from web3 import Web3
from dydx3 import constants

"""
This class DydxPClient is responsible for initializing the DydxClient instance.
It has a function __create_dydx_Instance() that is responsible for initializing the dydx instance and returning it.
"""


class DydxPClient(object):
    def __init__(self):
        self.client = None

    def create_dydx_Instance(self):
        self.client = Client(
            host=constants.API_HOST_MAINNET,
            network_id=constants.NETWORK_ID_MAINNET,
            web3=Web3(Web3.HTTPProvider(config("PROVIDER"))),
        )
        return self.client

    @property
    def get_dydx_instance(self):
        if self.client is not None:
            return self.client
        return self.create_dydx_Instance()

    def get_order_book(self, market="ETH-USD"):
        client = self.get_dydx_instance
        order_book = client.public.get_orderbook(
            market=market,
        )
        return order_book.data

    def get_historical_data(self, market="ETH-USD"):
        # effective_before_or_at	(Optional): Set a date by which the historical funding rates had to be created.
        effective_before_or_at = str(
            datetime.utcnow().replace(hour=12, day=1, month=1, year=2022)
        )
        client = self.get_dydx_instance
        historical_funding = client.public.get_historical_funding(
            market=market, effective_before_or_at=effective_before_or_at
        )
        historical_funding = vars(historical_funding)
        return historical_funding["data"]


if __name__ == "__main__":
    d = DydxPClient()
    print(d.get_historical_data(market="BTC-USD"))
