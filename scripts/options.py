import math
import time
import matplotlib.pyplot as plt
import numpy as np

from components import BlackScholesOptionPricing


class Options(object):
    TOKENS = ["ETH", "BTC"]
    PRICE_DIFF_TO_OPTION_PRICE_RATIO = {
        "ETH": [
            {"min": 300, "max": 700, "option_market_price_ratio": 0.0122},
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
        current_reserve=60000,
        optimal_utilization_ratio=0.7,
    ):
        self.optimal_utilization_ratio = optimal_utilization_ratio
        self.current_reserve = current_reserve
        self.token = token
        self.current_asset_price = current_asset_price
        self.underlying_asset_price = underlying_asset_price
        self.asset_vol = asset_vol
        self.option_market_price = option_market_price
        self.strike_price = strike_price
        self.price_floor = price_floor

    FUNDING_FEES = []
    UTILIZATION_RATES = []

    def plot_graph(self):

        xpoints = np.array(self.UTILIZATION_RATES)
        ypoints = np.array(self.FUNDING_FEES)

        plt.ylim(0, 200)
        plt.xlim(0, 100)

        plt.ylabel("Funding fee")
        plt.xlabel("Utilization %age")

        plt.plot(xpoints, ypoints)
        plt.vlines(
            x=70,
            ymin=0,
            ymax=200,
            colors="red",
            label=f"Optimal Utilization: {self.optimal_utilization_ratio * 100} %",
        )
        plt.legend()
        plt.show()

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

        strike_ratio = 2
        total_options_fee = 0
        funding_fee = 0

        for i in range(1, period):
            option_fee = (1 / (strike_ratio * i)) * (option_market_price)
            total_options_fee += option_fee
            funding_fee += option_fee - payoff

        funding_fee_object = {
            "strike_price": strike_price,
            "funding_fee": funding_fee,
            "asset_price": asset_price,
            "option_market_price": option_market_price,
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
            max_asset_price = 3400
        increase_by = 0.1
        total_funding_fees_object = {}
        current_asset_price = self.current_asset_price
        options_count = 0

        all_open_options_price = 0
        while current_asset_price <= max_asset_price:
            print("current_asset_price: ", current_asset_price)
            new_strike_price = self.price_floor * current_asset_price * self.asset_vol
            all_open_options_price += new_strike_price
            print("NEW_SP: ", new_strike_price)
            option_market_price = self._get_option_market_price(
                new_strike_price, current_asset_price
            )
            print("option_market_price: ", option_market_price)
            option_market_price = option_market_price

            funding_fee_object = self.get_total_funding_fee(
                option_market_price,
                period,
                new_strike_price,
                underlying_asset_price=current_asset_price,
            )
            total_funding_fees_object.update(funding_fee_object)
            current_asset_price += increase_by * current_asset_price
            options_count += 1
            # time.sleep(2)
        total_funding_fees_object["options_count"] = options_count
        total_funding_fees_object["all_open_options_price"] = all_open_options_price
        return total_funding_fees_object

    def _get_option_market_price(self, strike_price, current_asset_price):
        black_scholes = BlackScholesOptionPricing(
            current_asset_price=current_asset_price,
            strike_price=strike_price,
            risk_free_rate=0.2,
            option_expiration=1,
            sigma=0.3,
        )
        black_scholes_put_option_price = black_scholes.get_put_option_price()
        return black_scholes_put_option_price

    def _get_payoff(self, strike_price, current_asset_price):
        spot = current_asset_price
        payoff = max(strike_price - spot, 0)
        return payoff

    def update_funding_fee(
        self,
        current_funding_fee,
        all_open_options_price,
        current_reserve,
        total_reserve_drop_ratio,
    ):
        """
        Updating the funding fee of a user for their hedged asset by
        computing a certain interest rate on the funding fee as and when the current_reserve gets depleted because of
        closing options at the time of withdrawal.

        @params:
        current_funding_fee: Funding fee for the first option that was opened for the given user
        all_open_options_price: Sum of strike prices of all open options (Perp Vault size)
        current_reserve: Total usdc present in our pool
        total_reserve_drop_ratio: A static value with which the reserve is depleting | meant for testing purposes.
        """
        updated_funding_fee = current_funding_fee
        total_reserve = self._get_total_reserve(
            all_open_options_price, current_reserve
        )  # total_reserve is the sum of Perp Vault Size and current_reserve

        self.FUNDING_FEES.append(
            current_funding_fee
        )  # Appending all decreasing reserve values for plotting on the graph
        self.UTILIZATION_RATES.append(
            0
        )  # Appending 0 as the current reserve utilization ration values for plotting on the graph

        utilization_ratio = (
            0  # all_open_options_price / (all_open_options_price + current_reserve)
        )

        while (utilization_ratio * 100) < 100:
            total_reserve -= total_reserve_drop_ratio * total_reserve

            utilization_ratio = self._get_utilization_ratio(
                all_open_options_price, total_reserve
            )  # all_open_options_price / total_reserve

            self.UTILIZATION_RATES.append(
                utilization_ratio * 100
            )  # Appending current reserve utilization ration values for plotting on the graph

            interest_rate_below_optimal = self._get_interest_rate(
                below_optimal=True
            )  # R Slope 1 - Interest rate applied on funding fee when total_reserve is below optimal utilization
            interest_rate_above_optimal = self._get_interest_rate(
                below_optimal=False
            )  # R Slope 2 - Interest rate applied on funding fee when total_reserve is above optimal utilization

            if (
                utilization_ratio < self.optimal_utilization_ratio
            ):  # Read more about this on cruize docs section: funding-rate
                updated_funding_fee += (
                    utilization_ratio / self.optimal_utilization_ratio
                ) * interest_rate_below_optimal
            else:
                updated_funding_fee += interest_rate_below_optimal + (
                    (
                        (
                            (utilization_ratio - self.optimal_utilization_ratio)
                            / (1 - self.optimal_utilization_ratio)
                        )
                        * interest_rate_above_optimal
                    )
                )

            self.FUNDING_FEES.append(
                updated_funding_fee
            )  # Appending all new funding fee values for plotting on the graph
        return updated_funding_fee

    def _get_interest_rate(self, below_optimal=True):
        if below_optimal:
            return 4
        return 75

    def _get_utilization_ratio(self, all_open_options_price, total_reserve):
        utilization_ratio = all_open_options_price / total_reserve
        return utilization_ratio

    def _get_total_reserve(self, all_open_options_price, current_reserve):
        return all_open_options_price + current_reserve


if __name__ == "__main__":
    from pprint import pprint

    op = Options(
        token="ETH",
        current_asset_price=2938.53,
        underlying_asset_price=10000,
        asset_vol=1,
        option_market_price=1,
        strike_price=None,
        price_floor=0.85,
        optimal_utilization_ratio=0.7,
    )
    funding_fees_object = op.get_total_funding_fee_with_dynamic_strike_price(period=7)
    print("current_funding_fee:")
    pprint(funding_fees_object)
    current_reserve = 80000
    total_reserve = current_reserve + funding_fees_object["all_open_options_price"]
    updated_funding_fee = op.update_funding_fee(
        current_funding_fee=funding_fees_object["funding_fee"],
        all_open_options_price=funding_fees_object["all_open_options_price"],
        current_reserve=current_reserve,
        total_reserve_drop_ratio=0.1,
    )
    print("updated_funding_fee: ", updated_funding_fee)
    op.plot_graph()
