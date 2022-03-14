import time


class Options(object):
    TOKENS = ["ETH", "BTC"]
    PRICE_DIFF_TO_OPTION_PRICE_RATIO = {
        "ETH": [
            {"min": 300, "max": 500, "option_market_price_ratio": 0.0122},
            {"min": 100, "max": 299, "option_market_price_ratio": 0.00887254901},
            {"min": 1, "max": 99, "option_market_price_ratio": 0.00687254901},
            # {"min": 100, "max": 200, "option_price_ratio": 0.0048654301},
            # {"min": 100, "max": 200, "option_price_ratio": 0.002874},
        ]
    }

    def __init__(
        self,
        token,
        current_asset_price,
        asset_vol,
        price_floor,
        underlying_asset_price=None,
        option_market_price=None,
        strike_price=None,
    ):
        self.token = token
        self.current_asset_price = current_asset_price
        self.underlying_asset_price = underlying_asset_price
        self.asset_vol = asset_vol
        self.option_market_price = option_market_price
        self.strike_price = strike_price
        self.price_floor = price_floor

    def get_total_funding_fee(
        self,
        option_market_price,
        period,
        strike_price=None,
        underlying_asset_price=None,
    ):
        """
        @params:
        option_market_price: Premium for an option
        strike_price: Price of the asset for which an option will be minted
        underlying_asset_price: Price of the asset when the option is exercised

        This function computed the total_funding fee that a user pays over a given period
        to keep the options on their hedged asset alive i.e protected
        If the funding fee stops coming in, part of asset is liquidated to recuperate the missing funding fee.

        **Read more about this on cruize docs**
        """

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
            funding_fee += option_fee - payoff

        funding_fee_object = {
            "funding_fee": funding_fee,
        }
        return funding_fee_object

    def get_total_funding_fee_with_dynamic_strike_price(
        self, period, max_asset_price=None, min_asset_price=None
    ):
        """
        To compute a total funding fee based on the volatility of an asset, this function immitates a rise of 10% and
        a fall of 10% over a given period until it reaches a limit
        """
        # TODO:: use the internal historical data script for an asset and accumulate prices more closer to real world
        #  data -- Will come in by the end of this week (22nd March)
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
        diff = abs(strike_price - current_asset_price)
        option_market_price_ratio = 1
        print("diff: ", diff)

        option_market_price_ratios = self.PRICE_DIFF_TO_OPTION_PRICE_RATIO[self.token]
        for ratio in option_market_price_ratios:
            if ratio["min"] <= diff <= ratio["max"]:
                option_market_price_ratio = ratio["option_market_price_ratio"]

        return option_market_price_ratio

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
