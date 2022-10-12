import math

import numpy as np

from hedge_scripts.Short_only.interval import Interval


class ParameterManager(object):
    # auxiliary functions
    @staticmethod
    def define_target_prices(stgy_instance, slippage, vol, floor, trailing):
        mu = vol[0]
        sigma = vol[1]
        p_open_close = floor * (1 + slippage) * (1 + mu + 2 * sigma)
        p_trailing = floor * (1 - trailing)
        ##########################################################
        # We define the intervals
        list_of_intervals = ["open_close",
                             "floor",
                             "trailing_stop",
                             "ltv_limit"]
        list_of_trigger_prices = [p_open_close,
                                  floor,
                                  p_trailing,
                                  stgy_instance.aave.price_to_ltv_limit]
        # We define/update trigger prices
        for i in range(len(list_of_intervals)):
            interval_name = list_of_intervals[i]
            trigger_price = list_of_trigger_prices[i]
            stgy_instance.trigger_prices[interval_name] = trigger_price

    @staticmethod
    def define_intervals(stgy_instance):
        stgy_instance.intervals = {"infty": Interval(stgy_instance.trigger_prices['open_close'],
                                                     math.inf,
                                                     "infty", 0),
                                   "open_close": Interval(stgy_instance.trigger_prices['floor'],
                                                          stgy_instance.trigger_prices['open_close'],
                                                          "open_close", 1),
                                   "floor": Interval(stgy_instance.trigger_prices['trailing_stop'],
                                                     stgy_instance.trigger_prices['floor'],
                                                     "floor", 2),
                                   "trailing_stop": Interval(stgy_instance.trigger_prices['ltv_limit'],
                                                             stgy_instance.trigger_prices['trailing_stop'],
                                                             "trailing_stop", 3),
                                   "minus_infty": Interval(-math.inf,
                                                           stgy_instance.trigger_prices['ltv_limit'],
                                                           "minus_infty", 4)}

    # function to assign interval_current to each market_price in historical data
    @staticmethod
    def find_interval(stgy_instance, market_price):
        for i in list(stgy_instance.intervals.values()):
            if i.left_border < market_price <= i.right_border:
                return {"interval": i, "interval_name": i.name}

    @staticmethod
    def find_oc(current_oc, ocs, vol):
        mu, sigma = vol
        oc_up = current_oc * (1 + slippage) * (1 + mu + 2 * sigma)
        oc_down = current_oc * (1 + slippage) * (1 + mu - 2 * sigma)
        distances = []
        next_oc_up = []
        next_oc_down = []
        for i in range(len(ocs)):
            oci = ocs[i]
            if oc_up < oci:
                next_oc_up.append(oci)
                # ocs['up'].append(oci)
            elif oc_down > oci:
                next_oc_down.append(oci)
                # ocs['down'].append(oci)
            distances.append(current_oc - oci)
        # If we get here then we didnt return anything, so we return the farthest oc
        # Furthest down (positive distance current_oc > oci)
        max_value = max(distances)
        max_index = distances.index(max_value)
        # Furthest up (negative distance current_oc < oci)
        min_value = min(distances)
        min_index = distances.index(min_value)
        # print(next_oc_up)
        # print(next_oc_down)
        return {'up_choices': next_oc_up,
                'down_choices': next_oc_down,
                'max_distance_up': ocs[min_index],
                'max_distance_down': ocs[max_index]}

    @staticmethod
    def load_intervals(stgy_instance):
        stgy_instance.historical_data["interval"] = [[0, 0]] * len(stgy_instance.historical_data["close"])
        stgy_instance.historical_data["interval_name"] = ['nan'] * len(stgy_instance.historical_data["close"])
        for loc in range(len(stgy_instance.historical_data["close"])):
            market_price = stgy_instance.historical_data["close"][loc]
            for i in list(stgy_instance.intervals.values()):
                if i.left_border < market_price <= i.right_border:
                    stgy_instance.historical_data["interval"][loc] = i
                    stgy_instance.historical_data["interval_name"][loc] = i.name

    @staticmethod
    def calc_vol(last_date, data):
        periods_for_vol = [6 * 30 * 24 * 60, 3 * 30 * 24 * 60, 1 * 30 * 24 * 60]
        last_six_months = data.loc[:last_date][-periods_for_vol[0]:]
        for i in range(len(periods_for_vol)):
            N = periods_for_vol[i]
            log_returns = np.log(last_six_months[-N:]['close']) - np.log(last_six_months[-N:]['close'].shift(1))
            globals()['sigma_' + str(i)] = log_returns.ewm(alpha=0.8, adjust=False).std().mean()
            globals()['mu_' + str(i)] = log_returns.ewm(alpha=0.8, adjust=False).mean().mean()
        mu = mu_0 * 0.1 + mu_1 * 0.3 + mu_2 * 0.6
        sigma = sigma_0 * 0.1 + sigma_1 * 0.3 + sigma_2 * 0.6
        vol = [mu, sigma]
        return vol

    @staticmethod
    # Checking and updating data
    def update_parameters(stgy_instance, new_market_price, new_interval_current):
        # AAVE
        stgy_instance.aave.market_price = new_market_price
        stgy_instance.aave.interval_current = new_interval_current
        # Before updating collateral and debt we have to calculate last earned fees + update interests earned until now
        # As we are using hourly data we have to convert anual rate interest into hourly interest, therefore freq=365*24
        stgy_instance.aave.lending_fees_calc(freq=365 * 24 * 60)
        stgy_instance.aave.borrowing_fees_calc(freq=365 * 24 * 60)
        # We have to execute track_ first because we need the fees for current collateral and debt values
        stgy_instance.aave.track_lend_borrow_interest()
        # stgy_instance.aave.update_costs() # we add lend_borrow_interest to costs
        stgy_instance.aave.update_debt()  # we add the last borrowing fees to the debt
        stgy_instance.aave.update_collateral()  # we add the last lending fees to the collateral and update both eth and usd values
        stgy_instance.aave.ltv = stgy_instance.aave.ltv_calc()

        # DYDX
        stgy_instance.dydx.market_price = new_market_price
        stgy_instance.dydx.interval_current = new_interval_current
        stgy_instance.dydx.notional = stgy_instance.dydx.notional_calc()
        stgy_instance.dydx.equity = stgy_instance.dydx.equity_calc()
        stgy_instance.dydx.leverage = stgy_instance.dydx.leverage_calc()
        stgy_instance.dydx.pnl = stgy_instance.dydx.pnl_calc()
        # stgy_instance.dydx.price_to_liquidation = stgy_instance.dydx.price_to_liquidation_calc(stgy_instance.dydx_client)

    @staticmethod
    def reset_costs(stgy_instance):
        # We reset the costs in order to always start in 0
        stgy_instance.aave.costs = 0
        stgy_instance.dydx.costs = 0

    def find_scenario(self, stgy_instance, new_market_price, new_interval_current, interval_old, index):
        actions = self.actions_to_take(stgy_instance, new_interval_current, interval_old)
        self.simulate_fees(stgy_instance)
        time = 0
        time_aave = 0
        time_dydx = 0
        for action in actions:
            # if action == "rtrn_usdc_n_rmv_coll_dydx":
            #     time = stgy_instance.dydx.remove_collateral_dydx(new_market_price, new_interval_current, stgy_instance)
            #     stgy_instance.aave.return_usdc(new_market_price, new_interval_current, stgy_instance)
            if action == "borrow_usdc_n_add_coll":
                time_aave = stgy_instance.aave.borrow_usdc(stgy_instance)
                market_price = stgy_instance.historical_data["close"][index + time_aave]
                interval_current = stgy_instance.historical_data["interval"][index + time_aave]
                time_dydx = stgy_instance.dydx.add_collateral(stgy_instance)
                time_aave = 0
            elif action in stgy_instance.aave_features["methods"]:
                time_aave = getattr(stgy_instance.aave, action)(stgy_instance)
            elif action in stgy_instance.dydx_features["methods"]:
                time_dydx = getattr(stgy_instance.dydx, action)(stgy_instance)
            time += time_aave + time_dydx
            # print(stgy_instance.aave_features["methods"])
            # print(stgy_instance.dydx_features["methods"])
        return time
        # stgy_instance.append(action)

    @staticmethod
    def actions_to_take(stgy_instance, new_interval_current, interval_old):
        actions = []

        # Case P increasing
        if interval_old.is_lower(new_interval_current):
            for i in reversed(range(new_interval_current.position_order, interval_old.position_order)):

                # CASE: open_close_1 APPROACH
                if list(stgy_instance.intervals.keys())[i + 1] == 'open_close':
                    actions.append('close_short')

                # CASE: open_close_1 APPROACH
                elif list(stgy_instance.intervals.keys())[i + 1] == 'trailing_stop':
                    actions.append('close_short')

                # CASE: TOO MANY FEES FOR open_close_1 APPROACH
                #                 if list(stgy_instance.intervals.keys())[i+1] == 'open_close_2':
                #                     actions.append('close_short')

                else:
                    actions.append(list(stgy_instance.intervals.keys())[
                                       i + 1])  # when P goes up we execute the name of previous intervals
                # print(list(stgy_instance.intervals.keys())[i+1])

        # Case P decreasing
        else:
            for i in range(interval_old.position_order + 1, new_interval_current.position_order + 1):

                # In both cases we open at open_close_1 bc for open_close_2 case we manage the opening
                # from inside the for loop of the run_sims
                if list(stgy_instance.intervals.keys())[i] == 'open_close':
                    actions.append('open_short')

                elif list(stgy_instance.intervals.keys())[i] == 'trailing_stop':
                    actions.append('open_short')

                else:
                    actions.append(list(stgy_instance.intervals.keys())[i])
        # print(actions)
        return actions

    @staticmethod
    def simulate_fees(stgy_instance):
        # stgy_instance.gas_fees = round(random.choice(list(np.arange(1, 10, 0.5))), 6)

        # best case
        # stgy_instance.gas_fees = 1

        # stgy_instance.gas_fees = 3

        # stgy_instance.gas_fees = 6

        # worst case
        stgy_instance.gas_fees = 10

    @staticmethod
    def update_pnl(stgy_instance):
        stgy_instance.total_pnl = stgy_instance.total_pnl - stgy_instance.aave.costs - stgy_instance.dydx.costs + stgy_instance.aave.lending_fees_usd - stgy_instance.aave.borrowing_fees

    @staticmethod
    def add_costs(stgy_instance):
        stgy_instance.total_costs_from_aave_n_dydx = stgy_instance.total_costs_from_aave_n_dydx \
                                                     + stgy_instance.aave.costs + stgy_instance.dydx.costsnce.dydx.short_costs