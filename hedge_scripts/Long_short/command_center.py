import os
import json


from hedge_scripts.Short_only.stgyapp import StgyApp


def run_sim(period, slippage, floor, pcg):
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
    # Now we define prices and intervals given K and vol
    stgy.parameter_manager.define_target_prices(stgy, slippage, vol, floor, pcg)
    #########################
    # Save historical data with trigger prices and thresholds loaded
    # checking if the directory demo_folder
    # exist or not.
    if not os.path.exists("Files/From_%s_to_%s_open_close_at_%s" % (period[0], period[1], floor)):
        # if the demo_folder directory is not present
        # then create it.
        os.makedirs("Files/From_%s_to_%s_open_close_at_%s" % (period[0], period[1], floor))
    stgy.historical_data.to_csv("Files/From_%s_to_%s_open_close_at_%s/stgy.historical_data.csv"
                                % (period[0], period[1], floor))
    #########################
    # Here we define initial parameters for AAVE and DyDx depending on the price at which we are starting simulations

    # Define initial and final index if needed in order to only run simulations in periods of several trigger prices
    # As we calculate vol using first week of data, we initialize simulations from that week on
    initial_index = 1

    # Stk eth
    stgy.stk = 1000000 / stgy.historical_data['close'][initial_index]

    # AAVE
    stgy.aave.market_price = stgy.historical_data['close'][initial_index]

    # What is the price at which we place the collateral in AAVE given our initial_index?
    stgy.aave.entry_price = stgy.aave.market_price
    # We place 90% of staked as collateral and save 10% as a reserve margin
    stgy.aave.collateral_eth = round(stgy.stk * 0.9, 3)
    stgy.aave.collateral_eth_initial = round(stgy.stk * 0.9, 3)
    stgy.reserve_margin_eth = stgy.stk * 0.1
    # We calculate collateral and reserve current value
    stgy.aave.collateral_usdc = stgy.aave.collateral_eth * stgy.aave.market_price
    stgy.reserve_margin_usdc = stgy.aave.reserve_margin_eth * stgy.aave.market_price

    # What is the usdc_status for our initial_index?
    stgy.aave.usdc_status = True
    stgy.aave.debt = (stgy.aave.collateral_eth_initial * stgy.aave.entry_price) * stgy.aave.borrowed_percentage
    stgy.aave.debt_initial = (stgy.aave.collateral_eth_initial * stgy.aave.entry_price) * stgy.aave.borrowed_percentage
    # debt_initial
    stgy.aave.price_to_ltv_limit = round(stgy.aave.entry_price * stgy.aave.borrowed_percentage / stgy.aave.ltv_limit(),
                                         3)
    # stgy.total_costs = 104

    # DyDx
    stgy.dydx.market_price = stgy.historical_data['close'][initial_index]
    # stgy.dydx.interval_current = stgy.historical_data['interval'][initial_index]
    stgy.dydx.short_collateral = stgy.aave.debt
    stgy.dydx.short_equity = stgy.dydx.short_equity_calc()
    stgy.dydx.short_collateral_status = True
    #########################
    # Clear previous csv data for aave and dydx
    stgy.data_dumper.delete_results(period, floor)
    #########################
    # add header to csv of aave and dydx
    stgy.data_dumper.add_header(period, floor)
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
        previous_market_price = stgy.historical_data["close"][i-1]
        market_price = stgy.historical_data["close"][i]
        #########################
        # Update parameters
        # First we update everything in order to execute scenarios with updated values
        # We have to update
        # AAVE: market_price, interval_current, lending and borrowing fees (and the diference),
        # debt value, collateral value and ltv value
        # DyDx: market_price, interval_current, notional, equity, leverage and pnl
        stgy.parameter_manager.update_parameters(stgy, market_price)
        ##############################
        stgy.parameter_manager.find_scenario(stgy, market_price, previous_market_price)
        ##############################
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
                                    period, floor,
                                    sheet=False)
        #########################
        # we increment index by the time consumed in executing actions
        # i += time_used
        i += 1
    return maker_fees_counter