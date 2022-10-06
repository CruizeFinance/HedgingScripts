import os
import pygsheets
import matplotlib.pyplot as plt
from scipy.stats import norm
import csv
import pandas as pd
import numpy as np
import json
import math
import random

from hedge_scripts.Short_only.stgyapp import StgyApp


def run_sim(period, open_close, slippage, max_txs, L):
    global ocs
    # Initialize everything
    with open("Files/StgyApp_config.json") as json_file:
        config = json.load(json_file)

    # Initialize stgyApp
    stgy = StgyApp(config)
    # Period of Simulations
    # period = ["2019-09-01","2019-12-31"]
    stgy.historical_data = historical_data.loc[period[0] + ' 00:00:00':period[1] + ' 00:00:00']
    # For vol updates we take all data up to the last date
    stgy.launch(config)
    # Load target_prices + intervals in stgy.historical_data
    # First we calculate weighted vol
    last_date = period[1] + ' 00:00:00'
    vol = stgy.parameter_manager.calc_vol(last_date, historical_data)
    mu, sigma = vol
    # floor just in order to get triger_price['open_close_1'] = open_close_1
    floor = open_close / ((1 + slippage) * (1 + mu + 2 * sigma))
    # Now we define prices and intervals given K and vol
    stgy.parameter_manager.define_target_prices(stgy, slippage, vol, floor)
    # We create five equidistant OCs
    oc1 = stgy.trigger_prices['open_close']
    # oc2 = oc1 * (1+6/2/100)
    ocs = [oc1]
    for i in range(1, 5):
        globals()["oc" + str(i + 1)] = oc1 * (1 + 0.03 / 5) ** i  # We define 5 OCs based on a top width of 3%
        ocs.append(globals()["oc" + str(i + 1)])
    # But we start with the first oc1
    stgy.trigger_prices['open_close'] = oc1
    stgy.parameter_manager.define_intervals(stgy)

    # print("Volatility:", vol)
    # print("Floor:", stgy.trigger_prices['floor'])
    # print("Open_close1:", oc1)
    # print("Open_close2:", oc2)
    # print("1-OC2/OC1 - 1:", 1-oc2/oc1)
    #########################
    # Save historical data with trigger prices and thresholds loaded
    # checking if the directory demo_folder
    # exist or not.
    if not os.path.exists("Files/From_%s_to_%s_open_close_at_%s" % (period[0], period[1], open_close)):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs("Files/From_%s_to_%s_open_close_at_%s" % (period[0], period[1], open_close))
    stgy.historical_data.to_csv("Files/From_%s_to_%s_open_close_at_%s/stgy.historical_data.csv"
                                % (period[0], period[1], open_close))
    #########################
    # Here we define initial parameters for AAVE and DyDx depending on the price at which we are starting simulations

    # Define initial and final index if needed in order to only run simulations in periods of several trigger prices
    # As we calculate vol using first week of data, we initialize simulations from that week on
    initial_index = 1

    # Stk eth
    stgy.stk = 1000000 / stgy.historical_data['close'][initial_index]

    # AAVE
    stgy.aave.market_price = stgy.historical_data['close'][initial_index]
    # stgy.aave.interval_current = stgy.historical_data['interval'][initial_index]
    stgy.aave.interval_current = stgy.parameter_manager.find_interval(stgy, stgy.aave.market_price)['interval']

    # What is the price at which we place the collateral in AAVE given our initial_index?
    stgy.aave.short_entry_price = stgy.aave.market_price
    # We place 90% of staked as collateral and save 10% as a reserve margin
    stgy.aave.collateral_eth = round(stgy.stk * 0.9, 3)
    stgy.aave.collateral_eth_initial = round(stgy.stk * 0.9, 3)
    stgy.reserve_margin_eth = stgy.stk * 0.1
    # We calculate collateral and reserve current value
    stgy.aave.collateral_usdc = stgy.aave.collateral_eth * stgy.aave.market_price
    stgy.reserve_margin_usdc = stgy.aave.reserve_margin_eth * stgy.aave.market_price

    # What is the usdc_status for our initial_index?
    stgy.aave.usdc_status = True
    stgy.aave.debt = (stgy.aave.collateral_eth_initial * stgy.aave.short_entry_price) * stgy.aave.borrowed_percentage
    stgy.aave.debt_initial = (stgy.aave.collateral_eth_initial * stgy.aave.short_entry_price) * stgy.aave.borrowed_percentage
    # debt_initial
    stgy.aave.price_to_ltv_limit = round(stgy.aave.short_entry_price * stgy.aave.borrowed_percentage / stgy.aave.ltv_limit(),
                                         3)
    # stgy.total_costs = 104

    # DyDx
    stgy.dydx.market_price = stgy.historical_data['close'][initial_index]
    # stgy.dydx.interval_current = stgy.historical_data['interval'][initial_index]
    stgy.dydx.interval_current = stgy.parameter_manager.find_interval(stgy, stgy.dydx.market_price)['interval']
    stgy.dydx.short_collateral = stgy.aave.debt
    stgy.dydx.short_equity = stgy.dydx.short_equity_calc()
    stgy.dydx.short_collateral_status = True
    #########################
    # Load interval_old
    # interval_old = stgy.historical_data['interval'][initial_index]
    interval_old = stgy.aave.interval_current
    #########################
    # Clear previous csv data for aave and dydx
    stgy.data_dumper.delete_results(stgy, period, open_close)
    #########################
    # add header to csv of aave and dydx
    stgy.data_dumper.add_header(stgy, period, open_close)
    ##################################
    # Run through dataset
    #########################
    # import time
    # # run simulations
    # starttime = time.time()
    # print('starttime:', starttime)
    # for i in range(initial_index, len(stgy.historical_data)):
    i = initial_index

    maker_fees_counter = []
    while (i < len(stgy.historical_data)):
        # for i in range(initial_index, len(stgy.historical_data)):
        # pass

        # We reset costs in every instance
        stgy.parameter_manager.reset_costs(stgy)
        # new_interval_previous = stgy.historical_data["interval"][i-1]
        interval_previous = stgy.parameter_manager.find_interval(stgy, stgy.historical_data['close'][i - 1])['interval']
        # new_interval_current = stgy.historical_data["interval"][i]
        interval_current = stgy.parameter_manager.find_interval(stgy, stgy.historical_data['close'][i])['interval']
        market_price = stgy.historical_data["close"][i]
        #########################
        # This case is when P crossed open_close_2 while increasing (therefore we had to close short), I_old = I_open_close_2,
        # but then it goes below open_close_2 again.
        # So before updating I_old the bot will read I_current = I_open_close_2 and I_old = I_open_close_2.
        # So in order to be protected we manage this case as it names indicates open_close_2:
        # we open and close at this price.
        # Note that this also includes a situation in which price crossed floor while decreasing and the it crosses it again going up
        # I_old = I_open_close_2 and before updating new I_old we have I_current= I_open_close_2.
        # But here we do nothing because short is still open.
        #         if (new_interval_current == stgy.intervals["open_close_2"]) & (interval_old == stgy.intervals["open_close_2"]):
        #             time_dydx = stgy_instance.dydx.open_short(new_market_price, new_interval_current, stgy)
        # We need to update interval_old BEFORE executing actions bc if not the algo could read the movement late
        # therefore not taking the actions needed as soon as they are needed
        if interval_previous != interval_current:
            interval_old = interval_previous
        # print(interval_old.name)
        #########################
        # Update parameters
        # First we update everything in order to execute scenarios with updated values
        # We have to update
        # AAVE: market_price, interval_current, lending and borrowing fees (and the diference),
        # debt value, collateral value and ltv value
        # DyDx: market_price, interval_current, notional, equity, leverage and pnl
        stgy.parameter_manager.update_parameters(stgy, market_price, interval_current)
        # Here we identify price movent direction by comparing current interval and old interval
        # and we also execute all the actions involved since last price was read
        time_used = stgy.parameter_manager.find_scenario(stgy, market_price, interval_current, interval_old, i)
        ##############################
        # We update vol and ocs if short_status = False
        # if not stgy.dydx.short_status:
        #     current_date = list(stgy.historical_data.index)[i]
        #     vol = stgy.parameter_manager.calc_vol(current_date, data_for_vol)
        #     mu, sigma = vol
        #     oc1 = floor * (1+slippage) * (1+mu+2*sigma)
        #     ocs = [oc1]
        #     for i in range(1,5):
        #         globals()["oc"+str(i+1)] = oc1 * (1+0.03/5)**i # We define 5 OCs based on a top width of 3%
        #         ocs.append(globals()["oc"+str(i+1)])
        #########################
        # If we executed more txs than hat_L*20 then we change to K_2
        if (stgy.dydx.maker_fees_counter >= max_txs):
            # stgy.historical_data = stgy.historical_data_OC2
            # print(stgy.dydx.maker_fees_counter)
            current_date = list(stgy.historical_data.index)[i]
            current_oc = stgy.trigger_prices['open_close']
            vol = stgy.parameter_manager.calc_vol(current_date, stgy.historical_data)
            ocs_choices = stgy.parameter_manager.find_oc(current_oc, ocs, vol)
            # if short = open and if there are up_choices available, we take the last option (the furthest)
            # if there isn't options we take max_distance
            # random.seed(4)
            if stgy.dydx.short_status:
                if len(ocs_choices['up_choices']) != 0:
                    stgy.trigger_prices['open_close'] = ocs_choices['up_choices'][0]
                    # oc_choice_up = random.choice(range(len(ocs_choices['up_choices'])))
                    # stgy.trigger_prices['open_close'] = ocs_choices['up_choices'][oc_choice_up]
                else:
                    pass
            # if short = close and if there are down_choices available, we take the first option (the furthest)
            # if there isn't options we take max_distance
            else:
                if len(ocs_choices['down_choices']) != 0:
                    stgy.trigger_prices['open_close'] = ocs_choices['down_choices'][-1]
                    # oc_choice_down = random.choice(range(len(ocs_choices['down_choices'])))
                    # stgy.trigger_prices['open_close'] = ocs_choices['down_choices'][oc_choice_down]
                else:
                    pass
            # If we didnt change oc we dont clean maker_fees_counter
            if current_oc != stgy.trigger_prices['open_close']:
                maker_fees_counter.append({'oc': stgy.trigger_prices['open_close'],
                                           'txs': stgy.dydx.maker_fees_counter,
                                           # 'index': i,
                                           'date': str(stgy.historical_data.index[i])})
                stgy.dydx.maker_fees_counter = 0
            stgy.parameter_manager.define_intervals(stgy)
        ########################
        # Funding rates
        # We add funding rates every 8hs (we need to express those 8hs based on our historical data time frequency)
        # Moreover, we nee.named to call this method after find_scenarios in order to have all costs updated.
        # Calling it before find_scenarios will overwrite the funding by 0
        # We have to check all the indexes between old index i and next index i+time_used
        # for index in range(i, i+time_used):
        if (i % (8 * 60) == 0) and (stgy.dydx.short_status):
            stgy.dydx.add_funding_rates()
            # stgy.total_costs = stgy.total_costs + stgy.dydx.funding_rates
        #########################
        # Add costs
        stgy.parameter_manager.add_costs(stgy)
        stgy.parameter_manager.update_pnl(stgy)
        #########################
        # Write data
        # We write the data into the google sheet or csv file acording to sheet value
        # (sheet = True --> sheet, sheet = False --> csv)
        stgy.data_dumper.write_data(stgy,
                                    interval_previous, interval_old, i, period, open_close,
                                    sheet=False)
        #########################
        # we increment index by the time consumed in executing actions
        # i += time_used
        i += 1
    return maker_fees_counter