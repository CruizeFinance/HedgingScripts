class Dydx(object):

    def __init__(self, config):
        # assert aave_class == isinstance(aave)
        self.market_price = config['market_price']

        # Short attributes
        self.short_entry_price = config['entry_price']
        self.short_size = config['short_size']
        self.short_collateral = config['collateral']
        self.short_notional = config['notional']
        self.short_equity = config['equity']
        self.short_leverage = config['leverage']
        self.short_pnl = config['pnl']
        self.short_collateral_status = config['collateral_status']
        self.short_status = config['short_status']
        self.short_costs = 0

        # Long attributes
        self.long_entry_price = config['entry_price']
        self.long_size = config['short_size']
        self.long_notional = config['notional']
        # self.long_equity = config['equity']
        # self.long_leverage = config['leverage']
        self.long_pnl = config['pnl']
        self.long_status = config['short_status']
        self.long_costs = 0

        self.order_status = True
        self.withdrawal_fees = 0.01 / 100
        self.funding_rates = 0
        self.maker_taker_fees = 0
        self.maker_fees_counter = 0


    # auxiliary functions
    # Short methods
    def short_pnl_calc(self):
        return self.short_size * (self.market_price - self.short_entry_price)

    def short_notional_calc(self):
        return abs(self.short_size) * self.market_price

    def short_equity_calc(self):
        return self.short_collateral + self.short_pnl_calc()

    def short_leverage_calc(self):
        if self.short_equity_calc() == 0:
            return 0
        else:
            return self.short_notional_calc() / self.short_equity_calc()

    # Long methods
    def long_pnl_calc(self):
        return self.long_size * (self.market_price - self.long_entry_price)

    def long_notional_calc(self):
        return abs(self.long_size) * self.market_price

    def price_to_repay_aave_debt_calc(self, pcg_of_debt_to_cover, aave_class_instance):
        return self.short_entry_price \
               + aave_class_instance.debt * pcg_of_debt_to_cover / self.short_size

    @staticmethod
    def price_to_liquidation_calc(dydx_client_class_instance):
        return dydx_client_class_instance.dydx_margin_parameters["liquidation_price"]

    def add_funding_rates(self):
        self.simulate_funding_rates()
        self.short_costs = self.short_costs - self.funding_rates * self.short_notional

    def simulate_funding_rates(self):
        # self.funding_rates = round(random.choice(list(np.arange(-0.0075/100, 0.0075/100, 0.0005/100))), 6)

        # best case
        # self.funding_rates = 0.0075 / 100

        # average -0.00443%

        # worst case
        self.funding_rates = -0.0075 / 100

    def simulate_maker_taker_fees(self):
        # We add a counter for how many times we call this function
        # i.e. how many times we open and close the short
        self.maker_fees_counter += 1
        # self.maker_taker_fees = round(random.choice(list(np.arange(0.01/100, 0.035/100, 0.0025/100))), 6)

        # maker fees
        self.maker_taker_fees = 0.05 / 100  # <1M
        # self.maker_taker_fees = 0.04 / 100 # <5M
        # self.maker_taker_fees = 0.035 / 100 # <10M
        # self.maker_taker_fees = 0.03 / 100 # <50M
        # self.maker_taker_fees = 0.025 / 100 # <200M
        # self.maker_taker_fees = 0.02 / 100  # >200M

    # Actions to take
    def remove_collateral(self, stgy_instance):
        self.cancel_order()
        time = 0
        if self.short_collateral_status:
            self.short_collateral_status = False
            withdrawal_fees = self.short_collateral * self.withdrawal_fees
            self.short_collateral = 0
            # self.price_to_liquidation = 0

            # fees
            self.short_costs = self.short_costs + withdrawal_fees

            time = 1
        return time

    def open_short(self, stgy_instance):
        aave_class_instance = stgy_instance.aave
        # dydx_client_class_instance = stgy_instance.dydx_client
        if (not self.short_status) and self.order_status:
            self.short_status = True
            self.short_entry_price = self.market_price
            self.short_size = -aave_class_instance.collateral_eth_initial
            # self.collateral = aave_class_instance.debt_initial
            self.short_notional = self.short_notional_calc()
            self.short_equity = self.short_equity_calc()
            self.short_leverage = self.short_leverage_calc()
            # Simulate maker taker fees
            self.simulate_maker_taker_fees()
            # Add costs
            self.short_costs = self.short_costs + self.maker_taker_fees * self.short_notional
        return 0

    def close_short(self, stgy_instance):
        if self.short_status:
            self.short_notional = self.short_notional_calc()
            self.short_equity = self.short_equity_calc()
            self.short_leverage = self.short_leverage_calc()
            self.short_pnl = self.short_pnl_calc()
            stgy_instance.total_pnl = stgy_instance.total_pnl + self.short_pnl
            # We update short parameters after the calculation of pnl
            self.short_entry_price = 0
            self.short_status = False
            self.short_size = 0
            self.simulate_maker_taker_fees()
            self.short_costs = self.short_costs + self.maker_taker_fees * self.short_notional
        return 0

    def open_long(self, stgy_instance):
        aave_class_instance = stgy_instance.aave
        # dydx_client_class_instance = stgy_instance.dydx_client
        if not self.long_status:
            self.long_status = True
            self.long_entry_price = self.market_price
            self.long_size = aave_class_instance.collateral_eth_initial
            # self.collateral = aave_class_instance.debt_initial
            self.long_notional = self.long_notional_calc()
            # Simulate maker taker fees
            self.simulate_maker_taker_fees()
            # Add costs
            self.long_costs = self.long_costs + self.maker_taker_fees * self.long_notional
        return 0

    def close_long(self, stgy_instance):
        if self.long_status:
            self.long_notional = self.long_notional_calc()
            self.long_pnl = self.long_pnl_calc()
            stgy_instance.total_pnl = stgy_instance.total_pnl + self.long_pnl
            # We update short parameters after the calculation of pnl
            self.long_entry_price = 0
            self.long_status = False
            self.long_size = 0
            self.simulate_maker_taker_fees()
            self.long_costs = self.long_costs + self.maker_taker_fees * self.long_notional
        return 0

    def place_order(self, price):
        self.order_status = True
        # self.

    def cancel_order(self):
        self.order_status = False