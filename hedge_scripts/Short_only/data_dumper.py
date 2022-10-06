import csv
import os

import pygsheets

from hedge_scripts.Short_only.interval import Interval


class DataDamperNPlotter:
    def __init__(self):
        self.historical_data = None

    @staticmethod
    def write_data(stgy_instance,
                   new_interval_previous, interval_old, mkt_price_index, period, oc1,
                   sheet=False):
        aave_instance = stgy_instance.aave
        dydx_instance = stgy_instance.dydx
        data_aave = []
        data_dydx = []
        aave_wanted_keys = [
            "market_price",
            "interval_current",
            "entry_price",
            "collateral_eth",
            "usdc_status",
            "debt",
            "ltv",
            "lending_rate",
            "interest_on_lending_usd",
            "borrowing_rate",
            "interest_on_borrowing",
            "lend_minus_borrow_interest",
            "costs"]

        for i in range(len(aave_instance.__dict__.values())):
            if list(aave_instance.__dict__.keys())[i] in aave_wanted_keys:
                # print(list(aave_instance.__dict__.keys())[i])
                if isinstance(list(aave_instance.__dict__.values())[i], Interval):
                    data_aave.append(str(list(aave_instance.__dict__.values())[i].name))
                    # data_aave.append(new_interval_previous.name)
                    data_aave.append(interval_old.name)
                else:
                    data_aave.append(str(list(aave_instance.__dict__.values())[i]))
        for i in range(len(dydx_instance.__dict__.values())):
            if isinstance(list(dydx_instance.__dict__.values())[i], Interval):
                data_dydx.append(str(list(dydx_instance.__dict__.values())[i].name))
                # data_dydx.append(new_interval_previous.name)
                data_dydx.append(interval_old.name)
            else:
                data_dydx.append(str(list(dydx_instance.__dict__.values())[i]))
        # We add the index number of the appareance of market price in historical_data.csv order to find useful test values quicker
        data_aave.append(stgy_instance.gas_fees)
        data_aave.append(stgy_instance.total_costs_from_aave_n_dydx)
        data_aave.append(stgy_instance.total_pnl)
        data_aave.append(mkt_price_index)

        data_dydx.append(stgy_instance.gas_fees)
        data_dydx.append(stgy_instance.total_costs_from_aave_n_dydx)
        data_dydx.append(stgy_instance.total_pnl)
        data_dydx.append(mkt_price_index)
        # print(interval_old.name)
        # print(data_dydx, list(dydx_instance.__dict__.keys()))
        if sheet == True:
            gc = pygsheets.authorize(service_file=
                                     'stgy-1-simulations-e0ee0453ddf8.json')
            sh = gc.open('aave/dydx simulations')
            sh[0].append_table(data_aave, end=None, dimension='ROWS', overwrite=False)
            sh[1].append_table(data_dydx, end=None, dimension='ROWS', overwrite=False)
        else:
            path_to_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
            period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
            path_to_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
            period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
            with open(path_to_aave, 'a') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_aave)
            with open(path_to_dydx, 'a',
                      newline='', encoding='utf-8') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_dydx)

    @staticmethod
    def delete_results(stgy_instance, period, oc1):
        file_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
        period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
        file_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
        period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
        if (os.path.exists(file_aave) and os.path.isfile(file_aave)):
            os.remove(file_aave)
        if (os.path.exists(file_dydx) and os.path.isfile(file_dydx)):
            os.remove(file_dydx)

    @staticmethod
    def add_header(stgy_instance, period, oc1):
        aave_headers = [
            "market_price",
            "I_current",
            # "I_previous",
            "I_old",
            "entry_price",
            "collateral_eth",
            "usdc_status",
            "debt",
            "ltv",
            "lending_rate",
            "interest_on_lending_usd",
            "borrowing_rate",
            "interest_on_borrowing",
            "lend_minus_borrow_interest",
            "costs",
            "gas_fees",
            "total_costs_from_aave_n_dydx",
            "total_stgy_pnl",
            "index_of_mkt_price"]
        dydx_headers = [
            "market_price",
            "I_current",
            # "I_previous",
            "I_old",
            "entry_price",
            "short_size",
            "collateral",
            "notional",
            "equity",
            "leverage",
            "pnl",
            # "price_to_liquidation",
            "collateral_status",
            "short_status",
            "order_status",
            "withdrawal_fees",
            "funding_rates",
            "maker_taker_fees",
            "maker_fees_counter",
            "costs",
            "gas_fees",
            "total_costs_from_aave_n_dydx",
            "total_stgy_pnl",
            "index_of_mkt_price"]

        path_to_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
        period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
        path_to_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
        period[0], period[1], int(oc1))  # int(stgy_instance.trigger_prices['open_close']))
        with open(path_to_aave, 'a') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(aave_headers)
        with open(path_to_dydx, 'a',
                  newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(dydx_headers)