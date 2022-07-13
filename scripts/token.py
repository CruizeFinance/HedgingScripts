from scripts import interval


class Token(object):

    def __init__(self,
                 name,
                 price,
                 historical_volatility,
                 interval_current):
        assert isinstance(interval_current, interval.Interval)
        self.name = name
        self.price = price
        self.historical_volatility = historical_volatility
        self.interval_current = interval_current

    def returns_calc(self, historical_prices):
        return round(historical_prices.pct_change(),3)

    def historical_drift(self, historical_prices):
        return np.mean(self.returns_calc(historical_prices))

    def historical_volatility(self, historical_prices):
        return np.std(self.returns_calc(historical_prices))

    def update(self, p, interval_current):
        assert isinstance(interval_current, interval.Interval)
        self.price = p
        self.interval_current = interval_current