import math
import random
import numpy as np
import interval


class Dydx(object):
    def __init__(self, config):
        # assert aave_class == isinstance(aave)
        self.market_price = config["market_price"]
        self.interval_current = config["interval_current"]
        self.entry_price = config["entry_price"]
        self.short_size = config["short_size"]
        self.collateral = config["collateral"]
        self.notional = config["notional"]
        self.equity = config["equity"]
        self.leverage = config["leverage"]
        self.pnl = config["pnl"]
        # self.price_to_liquidation = config['price_to_liquidation']
        self.collateral_status = config["collateral_status"]
        self.short_status = config["short_status"]
        self.order_status = True
        self.withdrawal_fees = 0.01 / 100
        self.funding_rates = 0
        self.maker_taker_fees = 0
        self.costs = 0
        # self.historical = pd.DataFrame()
        # self.aave_class_instance = aave_class_instance
        # self.staked_in_protocol = stk

    # auxiliary functions
    def pnl_calc(self):
        return self.short_size * (self.market_price - self.entry_price)

    def notional_calc(self):
        return abs(self.short_size) * self.market_price

    def equity_calc(self):
        return self.collateral + self.pnl_calc()

    def leverage_calc(self):
        if self.equity_calc() == 0:
            return 0
        else:
            return self.notional_calc() / self.equity_calc()

    def price_to_repay_aave_debt_calc(self, pcg_of_debt_to_cover, aave_class_instance):
        return (
            self.entry_price
            + aave_class_instance.debt * pcg_of_debt_to_cover / self.short_size
        )

    @staticmethod
    def price_to_liquidation_calc(dydx_client_class_instance):
        return dydx_client_class_instance.dydx_margin_parameters["liquidation_price"]

    def add_funding_rates(self):
        self.simulate_funding_rates()
        self.costs = self.costs - self.funding_rates

    def simulate_funding_rates(self):
        # self.funding_rates = round(random.choice(list(np.arange(-0.0075/100, 0.0075/100, 0.0005/100))), 6)

        # best case
        # self.funding_rates = 0.0075 / 100

        # average -0.00443%

        # worst case
        self.funding_rates = -0.0075 / 100

    def simulate_maker_taker_fees(self):
        # self.maker_taker_fees = round(random.choice(list(np.arange(0.01/100, 0.035/100, 0.0025/100))), 6)

        # maker fees
        self.maker_taker_fees = 0.05 / 100 # <1M
        # self.maker_taker_fees = 0.04 / 100 # <5M
        # self.maker_taker_fees = 0.035 / 100 # <10M
        # self.maker_taker_fees = 0.03 / 100 # <50M
        # self.maker_taker_fees = 0.025 / 100 # <200M
        # self.maker_taker_fees = 0.02 / 100  # >200M

    # Actions to take
    def remove_collateral(self, new_market_price, new_interval_current, stgy_instance):
        self.cancel_order()
        time = 0
        if self.collateral_status:
            self.collateral_status = False
            withdrawal_fees = self.collateral * self.withdrawal_fees
            self.collateral = 0
            # self.price_to_liquidation = 0

            # fees
            self.costs = self.costs + withdrawal_fees

            time = 1
        return time

    def add_collateral(self, new_market_price, new_interval_current, stgy_instance):
        gas_fees = stgy_instance.gas_fees
        aave_class_instance = stgy_instance.aave
        time = 0
        if not self.collateral_status:
            self.collateral_status = True
            self.collateral = aave_class_instance.debt_initial
            # fees
            self.costs = self.costs + gas_fees
            # We place an order in open_close
<<<<<<< HEAD
            self.place_order(stgy_instance.trigger_prices['open_close'])
=======
            self.place_order(stgy_instance.target_prices["open_close"])
>>>>>>> cd6cfcb... write function for getting order book and historical data
            # add time
            time = 10
        return time

    def open_short(self, new_market_price, new_interval_current, stgy_instance):
        aave_class_instance = stgy_instance.aave
        # dydx_client_class_instance = stgy_instance.dydx_client
        intervals = stgy_instance.intervals
        if (not self.short_status) and self.order_status:
            self.short_status = True
            # dydx parameters
<<<<<<< HEAD
            if self.market_price <= stgy_instance.trigger_prices['floor']:
                print("CAUTION: OPEN PRICE LESS OR EQUAL TO FLOOR!")
                print("Difference of: ", stgy_instance.trigger_prices['floor'] - self.market_price)

            # if self.market_price <= stgy_instance.trigger_prices['open_close']:
            #     print("CAUTION: OPEN PRICE LOWER THAN open_close!")
            #     print("Difference of: ", stgy_instance.trigger_prices['open_close'] - self.market_price)
=======
            if self.market_price <= stgy_instance.target_prices["floor"]:
                print("CAUTION: OPEN PRICE LESS OR EQUAL TO FLOOR!")
                print(
                    "Difference of: ",
                    stgy_instance.target_prices["floor"] - self.market_price,
                )

            if self.market_price <= stgy_instance.target_prices["open_close"]:
                print("CAUTION: OPEN PRICE LOWER THAN open_close!")
                print(
                    "Difference of: ",
                    stgy_instance.target_prices["open_close"] - self.market_price,
                )
>>>>>>> cd6cfcb... write function for getting order book and historical data
            self.entry_price = self.market_price
            self.short_size = -aave_class_instance.collateral_eth_initial
            # self.collateral = aave_class_instance.debt_initial
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            # Simulate maker taker fees
            self.simulate_maker_taker_fees()
            # Add costs
            self.costs = self.costs + self.maker_taker_fees * self.notional

            price_floor = intervals["open_close"].left_border
            floor_position = intervals["floor"].position_order

<<<<<<< HEAD
            price_floor = intervals['open_close'].left_border
            floor_position = intervals['floor'].position_order

            price_to_repay_debt = self.price_to_repay_aave_debt_calc(1 + aave_class_instance.buffer_for_repay(),
                                                                     aave_class_instance)
            price_to_ltv_limit = intervals['floor'].left_border
            stgy_instance.trigger_prices['repay_aave'] = price_to_repay_debt
            stgy_instance.trigger_prices['ltv_limit'] = price_to_ltv_limit
=======
            price_to_repay_debt = self.price_to_repay_aave_debt_calc(
                1 + aave_class_instance.buffer_for_repay(), aave_class_instance
            )
            price_to_ltv_limit = intervals["floor"].left_border
            stgy_instance.target_prices["repay_aave"] = price_to_repay_debt
            stgy_instance.target_prices["ltv_limit"] = price_to_ltv_limit
>>>>>>> cd6cfcb... write function for getting order book and historical data
            if price_to_ltv_limit < price_to_repay_debt:
                intervals["floor"] = interval.Interval(
                    price_to_repay_debt, price_floor, "floor", floor_position
                )
                intervals["repay_aave"] = interval.Interval(
                    price_to_ltv_limit,
                    price_to_repay_debt,
                    "repay_aave",
                    floor_position + 1,
                )
                intervals["minus_infty"] = interval.Interval(
                    -math.inf, price_to_ltv_limit, "minus_infty", floor_position + 2
                )
            else:
                print("CAUTION: P_ltv > P_repay")
                print("Difference of: ", price_to_ltv_limit - price_to_repay_debt)
                price_to_repay_debt = self.price_to_repay_aave_debt_calc(
                    0.5, aave_class_instance
                )
                intervals["floor"] = interval.Interval(
                    price_to_ltv_limit, price_floor, "floor", floor_position
                )
                intervals["ltv_limit"] = interval.Interval(
                    price_to_repay_debt,
                    price_to_ltv_limit,
                    "repay_aave",
                    floor_position + 1,
                )
                intervals["minus_infty"] = interval.Interval(
                    -math.inf, price_to_repay_debt, "minus_infty", floor_position + 2
                )
            self.order_status = False
        return 0

    def close_short(self, new_market_price, new_interval_current, stgy_instance):
        if self.short_status:
            # Next if is to move up the threshold if we didnt execute at exactly open_close
<<<<<<< HEAD
            if self.market_price >= stgy_instance.trigger_prices['open_close']:
                # new_open_close = self.market_price
                print("CAUTION: SHORT CLOSED AT A PRICE GREATER OR EQUAL TO CLOSE_SHORT!")
                print("Difference of: ", self.market_price - stgy_instance.trigger_prices['open_close'])
=======
            if self.market_price >= stgy_instance.target_prices["open_close"]:
                # new_open_close = self.market_price
                print(
                    "CAUTION: SHORT CLOSED AT A PRICE GREATER OR EQUAL TO CLOSE_SHORT!"
                )
                print(
                    "Difference of: ",
                    self.market_price - stgy_instance.target_prices["open_close"],
                )
>>>>>>> cd6cfcb... write function for getting order book and historical data
                # stgy_instance.target_prices['open_close'] = self.market_price
            self.notional = self.notional_calc()
            self.equity = self.equity_calc()
            self.leverage = self.leverage_calc()
            self.pnl = self.pnl_calc()
            # We update short parameters after the calculation of pnl
            self.entry_price = 0
            self.short_status = False
            self.short_size = 0
            self.simulate_maker_taker_fees()
            self.costs = self.costs + self.maker_taker_fees * self.notional
<<<<<<< HEAD
            self.place_order(stgy_instance.trigger_prices['open_close'])
        return 0
=======
            self.place_order(stgy_instance.target_prices["open_close"])
>>>>>>> cd6cfcb... write function for getting order book and historical data

    def place_order(self, price):
        self.order_status = True
        # self.

    def cancel_order(self):
        self.order_status = False
