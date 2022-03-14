import time

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd


class Options(object):
    TOKENS = ["ETH", "BTC"]
    PRICE_DIFF_TO_OPTION_PRICE_RATIO = {
        "ETH": [
            {"min": 201, "max": 500, "option_price_ratio": 0.0122},
            {"min": 100, "max": 200, "option_price_ratio": 0.00887254901},
        ]
    }

    def __init__(
        self,
        token,
        current_asset_price,
        underlying_asset_price,
        asset_vol,
        option_market_price,
        strike_price,
        price_floor,
    ):
        self.token = token
        self.current_asset_price = current_asset_price
        self.underlying_asset_price = underlying_asset_price
        self.asset_vol = asset_vol
        self.option_market_price = option_market_price
        self.strike_price = strike_price
        self.price_floor = price_floor

    def get_data(self):
        driver = webdriver.Chrome(
            "/Users/prithvirajmurthy/Desktop/blockchain/web_scrapper/chromedriver"
        )

        products = []  # List to store name of the product
        prices = []  # List to store price of the product
        ratings = []  # List to store rating of the product
        url = "https://www.flipkart.com/laptops/"
        driver.get(
            f"<a href={url}>https://www.flipkart.com/laptops/</a>~buyback-guarantee-on-laptops-/pr?sid=6bo%2Cb5g&amp;amp;amp;amp;amp;amp;amp;amp;amp;uniq"
        )
        content = driver.page_source
        soup = BeautifulSoup(content)
        for a in soup.findAll("a", href=True, attrs={"class": "_31qSD5"}):
            name = a.find("div", attrs={"class": "_3wU53n"})
        price = a.find("div", attrs={"class": "_1vC4OE _2rQ-NK"})
        rating = a.find("div", attrs={"class": "hGSR34 _2beYZw"})
        products.append(name.text)
        prices.append(price.text)
        ratings.append(rating.text)
        df = pd.DataFrame(
            {"Product Name": products, "Price": prices, "Rating": ratings}
        )
        df.to_csv("products.csv", index=False, encoding="utf-8")

    def get_total_funding_fee(
        self,
        option_market_price,
        period,
        strike_price=None,
        underlying_asset_price=None,
    ):
        asset_price = self.current_asset_price
        if underlying_asset_price:
            asset_price = underlying_asset_price

        if not strike_price:
            self.strike_price = asset_price * self.price_floor
        else:
            self.strike_price = strike_price
        payoff = self._get_payoff(self.strike_price, asset_price)
        print("payoff: ", payoff)
        strike_ratio = 2
        total_options_fee = 0
        funding_fee = 0
        for i in range(1, period):
            option_fee = (1 / (strike_ratio * i)) * (option_market_price)
            total_options_fee += option_fee
            funding_fee += total_options_fee - payoff
        funding_fee_object = {
            "funding_fee": funding_fee,
            "total_options_fee": total_options_fee,
        }
        return funding_fee_object

    def get_total_funding_fee_with_dynamic_strike_price(
        self, period, max_asset_price=None
    ):
        if not max_asset_price:
            max_asset_price = 3000
        increase_by = 0.1
        total_funding_fees_object = {}
        current_asset_price = self.current_asset_price
        options_count = 0

        while current_asset_price <= max_asset_price:
            print("current_asset_price: ", current_asset_price)
            new_strike_price = self.price_floor * current_asset_price * self.asset_vol
            print("NEW_SP: ", new_strike_price)
            option_market_price_ratio = self._get_option_market_price(
                new_strike_price, current_asset_price
            )
            print("option_market_price: ", option_market_price_ratio)
            option_market_price = new_strike_price * option_market_price_ratio

            funding_fee_object = self.get_total_funding_fee(
                option_market_price,
                period,
                new_strike_price,
                underlying_asset_price=current_asset_price,
            )
            total_funding_fees_object.update(funding_fee_object)
            current_asset_price += increase_by * current_asset_price
            options_count += 1
            time.sleep(2)
        total_funding_fees_object["options_count"] = options_count
        return total_funding_fees_object

    def _get_option_market_price(self, strike_price, current_asset_price):
        diff = strike_price - current_asset_price
        option_market_price_ratio = 1
        # price_bracket = self.ASSET_PRICE_BRACKET[self.token]
        # if diff > 0:
        print("diff: ", diff)
        if self.token == self.TOKENS[1]:
            if diff < 0:
                diff = abs(diff)
                if 1000 <= diff <= 8000:
                    option_market_price_ratio = 0.00007171428
            else:
                if 1500 <= diff < 2000:
                    option_market_price_ratio = 0.01
                elif 2000 <= diff < 3500:
                    option_market_price_ratio = 0.01072
                elif diff > 4000:
                    option_market_price_ratio = 0.009875

        else:
            print("ETH")
            if diff < 0:
                diff = abs(diff)
                if 100 <= diff < 400:
                    option_market_price_ratio = 0.00057516074
                if 400 <= diff < 700:
                    option_market_price_ratio = 0.00039632409
            else:
                if 200 <= diff < 500:
                    option_market_price_ratio = 0.14582857142
                if 100 <= diff < 200:
                    option_market_price_ratio = 0.09095185185
                elif diff < 0:
                    option_market_price_ratio = 0.00595064651

        return option_market_price_ratio

    def _get_options_market_prices_for_assets(self, assets=[]):
        pass

    def _get_payoff(self, strike_price, current_asset_price):
        spot = current_asset_price
        payoff = max(strike_price - spot, 0)
        return payoff


if __name__ == "__main__":
    op = Options(
        token="ETH",
        current_asset_price=2584,
        underlying_asset_price=10000,
        asset_vol=1,
        option_market_price=1,
        strike_price=None,
        price_floor=0.85,
    )
    # print('option price: ', op._get_option_market_price(2800, 2584))
    print(op.get_total_funding_fee_with_dynamic_strike_price(period=7))
