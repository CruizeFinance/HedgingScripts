from scripts import aave
from scripts import dydx_client


class Dydx(object):

    def __init__(self, config):
        # assert aave_class == isinstance(aave)
        self.market_price = config['market_price']
        self.interval_current = config['interval_current']
        self.entry_price = config['entry_price']
        self.short_size = config['short_size']
        self.collateral = config['collateral']
        self.notional = config['notional']
        self.equity = config['equity']
        self.leverage = config['leverage']
        self.pnl = config['pnl']
        self.price_to_liquidation = config['price_to_liquidation']
        self.collateral_status = config['collateral_status']
        self.short_status = config['short_status']
        # self.historical = pd.DataFrame()
        # self.aave_class_instance = aave_class_instance
        # self.staked_in_protocol = stk

    # auxiliary functions
    def pnl_calc(self):
        return self.short_size * (self.market_price-self.entry_price)

    def notional_calc(self):
        return abs(self.short_size)*self.market_price

    def equity_calc(self):
        return self.collateral + self.pnl(self.short_size,self.market_price)

    def leverage_calc(self):
        return self.notional_calc() / self.equity_calc()

    def price_to_repay_aave_debt_calc(self, pcg_of_debt_to_cover, aave_class_instance):
        return self.entry_price \
               + (aave_class_instance.debt + aave_class_instance.fees_function()) \
               * pcg_of_debt_to_cover / self.short_size

    @staticmethod
    def price_to_liquidation_calc(dydx_client_class_instance):
        return dydx_client_class_instance.dydx_margin_parameters["liquidation_price"]

    # Actions to take
    def remove_collateral_dydx(self, new_market_price, new_interval_current, aave_class_instance):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if self.collateral_status:
            self.collateral = False
            self.short_status = False
            # dydx parameters
            self.entry_price = 0
            self.short_size = 0
            self.collateral = 0
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            self.price_to_liquidation = 0

    def add_collateral_dydx(self, new_market_price, new_interval_current, aave_class_instance):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if not self.collateral_status:
            self.collateral_status = True
            self.short_status = False
            self.entry_price = 0
            self.short_size = 0
            self.collateral = aave_class_instance.debt
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            self.price_to_liquidation = 0

    def open_short(self, new_market_price, new_interval_current, aave_class_instance, dydx_client_class_instance):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if not self.short_status:
            self.collateral_status = True
            self.short_status = True
            # dydx parameters
            self.entry_price = self.market_price
            self.short_size = -aave_class_instance.collateral
            self.collateral = aave_class_instance.debt
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = 0
            self.price_to_liquidation = self.price_to_liquidation_calc(dydx_client_class_instance)

            price_to_repay_debt = self.price_to_repay_aave_debt_calc(self, 1.5, aave_class_instance)

    def close_short(self, new_market_price, new_interval_current, aave_class_instance):
        self.market_price = new_market_price
        self.interval_current = new_interval_current
        if self.short_status:
            self.short_status = False
            self.short_size = 0
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            self.price_to_liquidation = 0
