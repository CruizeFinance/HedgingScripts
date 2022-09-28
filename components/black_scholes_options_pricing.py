import numpy as np
from scipy.stats import norm

CDF = norm.cdf


class BlackScholesOptionPricing(object):
    def __init__(
        self,
        current_asset_price=None,
        strike_price=None,
        option_expiration=1,
        risk_free_rate=0.1,
        sigma=0.3,
    ):
        self.current_asset_price = current_asset_price
        self.strike_price = strike_price
        self.option_expiration = option_expiration
        self.risk_free_rate = risk_free_rate
        self.sigma = sigma

    def get_put_option_price(self):
        d1 = (
            np.log(self.current_asset_price / self.strike_price)
            + (self.risk_free_rate + self.sigma**2 / 2) * self.option_expiration
        ) / (self.sigma * np.sqrt(self.option_expiration))
        d2 = d1 - self.sigma * np.sqrt(self.option_expiration)
        return self.strike_price * np.exp(
            -self.risk_free_rate * self.option_expiration
        ) * CDF(-d2) - self.current_asset_price * CDF(-d1)


if __name__ == "__main__":
    current_asset_price = 2938.53
    strike_price = 2497.7505
    risk_free_rate = 0.2
    option_expiration = 1
    sigma = 0.3

    bs = BlackScholesOptionPricing(
        current_asset_price, strike_price, option_expiration, risk_free_rate, sigma
    )
    print("Calls: ", bs.get_put_option_price())
