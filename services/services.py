import requests


class Services(object):
    def get_token_price(self, token_symbol):
        url = f"https://api.coinbase.com/v2/prices/{token_symbol}-USD/spot"
        resp = requests.get(url).json()
        print(resp)
        token_price = resp["data"]["amount"]
        return token_price


if __name__ == "__main__":
    ser = Services()
    print(ser.get_token_price("BTC"))
