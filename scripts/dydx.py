from scripts import aave


class Dydx(object):

    def __init__(self, config):
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

    # auxiliary functions
    def pnl_calc(self):
        return self.short_size * (self.market_price-self.entry_price)

    def notional_calc(self):
        return abs(self.short_size)*self.market_price

    def equity_calc(self):
        return self.collateral + self.pnl(self.short_size,self.market_price)

    def leverage_calc(self):
        return self.notional_calc() / self.equity_calc()

    def price_to_repay_aave_debt_calc(self, aave_parameters, pcg_of_debt_to_cover):
        return self.entry_price + (aave_parameters['debt'] + aave.Aave(aave_parameters).fees_function()) * pcg_of_debt_to_cover / self.short_size
    
    # def add_historical(self, dydc_parameters):
    #     self.historical.append(dydc_parameters)

    # action functions
    def remove_collateral_dydx(self, interval_current, aave_parameters):
        short_status = False
        # dydx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = aave_parameters
        self.entry_price = 0
        self.short_size = 0
        collateral = 0
        self.notional = self.notional_calc()
        self.equity = self.equity_calc()
        self.leverage = self.leverage_calc()
        P_repay_debt = P_to_cover_AAVE_debt_function(self.short_size, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        dydx_parameters = [self.market_price, self.interval_current.name, self.short_size, equity,self.notional, L, P_repay_debt, short_status]

        return dydx_parameters

    def add_collateral_dydx(self, aave_parameters):
        short_status = False
        # dydx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = aave_parameters
        self.entry_price = 0
        self.short_size = 0
        self.collateral = Debt
        self.notional = self.notional_calc()
        self.equity = self.equity_calc()
        self.leverage = self.leverage_calc()
        P_repay_debt = P_to_cover_AAVE_debt_function(self.short_size, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        dydx_parameters = [self.market_price, self.interval_current.name, self.short_size,
                           self.equity, self.notional, self.leverage, P_repay_debt, self.short_status]

        return dydx_parameters

    def open_short(self, aave_parameters):
        self.short_status = True
        # dydx parameters
        p_AAVE, interval_AAVE, coll, Debt, LTV, P_LTV_AAVE, r_L, r_B, AAVE_strategy_status = aave_parameters
        self.entry_price = self.market_price
        self.short_size = -coll
        self.collateral = Debt
        self.notional = self.notional_calc()
        self.equity = self.equity_calc()
        self.leverage = self.leverage_calc()
        P_repay_debt = P_to_cover_AAVE_debt_function(self.short_size, coll, r_B, r_L,
                                                     1.5)  # We have to define the criteria for this price

        dydx_parameters = [self.market_price, self.interval_current.name, self.short_size,
                           self.equity, self.notional, self.leverage, P_repay_debt, self.short_status]

        return dydx_parameters

    def close_short(self):
        self.short_status = False
        # update profit parameters
        self.pnl = self.pnl_calc()
        self.equity = self.equity_calc()
        # close position
        self.short_size = 0
        self.notional = self.notional_calc()
        self.leverage = self.leverage_calc()
        P_repay_debt = 0

        dydx_parameters = [self.market_price, self.interval_current.name, self.short_size,
                           self.equity, self.notional, self.leverage, P_repay_debt, self.short_status]
        return dydx_parameters