import csv
import os

import pygsheets

from hedge_scripts.Short_only.interval import Interval


class DataDamperNPlotter:
    def __init__(self):
        self.historical_data = None

    @staticmethod
    def write_data(stgy_instance,
                   period, floor,
                   sheet=False):
        aave_instance = stgy_instance.aave
        dydx_instance = stgy_instance.dydx
        data_aave = []
        data_dydx = []
        aave_wanted_keys = [
            "market_price",
            # "interval_current",
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
                    data_aave.append(str(list(aave_instance.__dict__.values())[i]))
        for i in range(len(dydx_instance.__dict__.values())):
                data_dydx.append(str(list(dydx_instance.__dict__.values())[i]))
        # We add the index number of the appareance of market price in historical_data.csv order to find useful test values quicker
        data_aave.append(stgy_instance.gas_fees)
        data_aave.append(stgy_instance.total_costs_from_aave_n_dydx)
        data_aave.append(stgy_instance.total_pnl)

        data_dydx.append(stgy_instance.gas_fees)
        data_dydx.append(stgy_instance.total_costs_from_aave_n_dydx)
        data_dydx.append(stgy_instance.total_pnl)
        if sheet == True:
            gc = pygsheets.authorize(service_file=
                                     'stgy-1-simulations-e0ee0453ddf8.json')
            sh = gc.open('aave/dydx simulations')
            sh[0].append_table(data_aave, end=None, dimension='ROWS', overwrite=False)
            sh[1].append_table(data_dydx, end=None, dimension='ROWS', overwrite=False)
        else:
            path_to_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
            period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
            path_to_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
            period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
            with open(path_to_aave, 'a') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_aave)
            with open(path_to_dydx, 'a',
                      newline='', encoding='utf-8') as file:
                writer = csv.writer(file, lineterminator='\n')
                writer.writerow(data_dydx)

    @staticmethod
    def delete_results(period, floor):
        file_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
        period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
        file_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
        period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
        if (os.path.exists(file_aave) and os.path.isfile(file_aave)):
            os.remove(file_aave)
        if (os.path.exists(file_dydx) and os.path.isfile(file_dydx)):
            os.remove(file_dydx)

    @staticmethod
    def add_header(period, floor):
        aave_headers = [
            "market_price",
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
            "total_stgy_pnl"]
        dydx_headers = [
            "market_price",
            "short_entry_price",
            "short_size",
            "short_collateral",
            "short_notional",
            "short_equity",
            "short_leverage",
            "short_pnl",
            "short_collateral_status",
            "short_status",
            "short_costs",
            "long_entry_price",
            "long_size",
            "long_notional",
            "long_pnl",
            "long_status",
            "long_costs",
            "order_status",
            "withdrawal_fees",
            "funding_rates",
            "maker_taker_fees",
            "maker_fees_counter",
            "gas_fees",
            "total_costs_from_aave_n_dydx",
            "total_stgy_pnl"]

        path_to_aave = 'Files/From_%s_to_%s_open_close_at_%s/aave_results.csv' % (
        period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
        path_to_dydx = 'Files/From_%s_to_%s_open_close_at_%s/dydx_results.csv' % (
        period[0], period[1], int(floor))  # int(stgy_instance.trigger_prices['open_close']))
        with open(path_to_aave, 'a') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(aave_headers)
        with open(path_to_dydx, 'a',
                  newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow(dydx_headers)