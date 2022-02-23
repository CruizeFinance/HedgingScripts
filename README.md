# Data scripts
to analyze and test different models, algorithms and mock systems.

### Scripts written so far:
<li> Hedging fees <br>
Generated based on 
  number of days the protocol was open to risks due to the assets value and
  trading fees based on transactions in ETH/CRUIZE open pool in a dex.
File: /v1_profit_loss/views
  
<br><br>
`curl --location --request GET 'http://127.0.0.1:8000/revenue/v1?cruize_price=1&staked_asset_price=3000&dip_days=14&staked_eth_size=0.5&cover_pool=100000&current_price_of_asset=2400&tuner=0.2&transactions_per_day=500'`

<br>

<li> Smart Treasury - Mocked <br>
To maintain an 80/20 Cruize/USDC ratio by interacting with the open market to determine whether to selling or buy back cruize tokens.
<br>
File: /smart_treasury/views/

<br><br>
`curl --location --request GET 'http://127.0.0.1:8000/smart_treasury?usdc_pool=6000&cruize_pool=8000&lp_usdc=400&cruize_price=4'`

<br>

<li> Asset Historical data <br>
To generate an assets historical data with high and low price of asset 
for any given period. <br>
File: /tokens/views/historical_data
<br>
<br>

Example: 
Generating historical data on a day by day basis for the last 30 days 
will produce high and low value of the asset for each day. <br>
Similarly, data for a month by month basis for the last 6 months will produce high and low for each month in the last 6 months.
<br><br>
`curl --location --request GET 'http://127.0.0.1:8000/token_data/v1/historical_data/?token=BTC&conversion_token=USD&source=day&past_days=30'`

<br>

<li> Liquidation Threshold <br>
  Calculate Liquidation threshold for an asset based on high and low price of asset for 
  each month for a set of months in the past. <br>
  File: /tokens/views/liquidation_threshold

<br><br>
`curl --location --request GET 'http://127.0.0.1:8000/token_data/v1/liquidation_threshold/?token=BTC&conversion_token=USD&source=day&past_days=30'`

## How to run a script?
1. Clone the repo to your local computer.
2. Open the project on Pycharm
3. Create a conda environment: `conda create -n cr_scripts_venv python=3.7` <br>
   Activate the conda environment: `conda activate cr_scripts_venv`
4. Set it as the default Python Interpreter for the project.
5. Run `pip install -r requirements.txt`
6. Run `python manage.py runserver`