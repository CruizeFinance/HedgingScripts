import pandas as pd
import requests


class Deribit(object):
    url = "https://test.deribit.com/api/v2/public/"

    def get_order_book(self):
        url = self.url + "get_order_book"
        resp = requests.get(url, params={'depth': 50, 'instrument_name': 'ETH-PERPETUAL'})
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

if __name__ == '__main__':
    d = Deribit()
    order_book = d.get_order_book()
    d.create_csv(order_book)