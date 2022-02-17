# Data scripts
to analyze and test different models, algorithms and mock systems.

### Scripts written so far:
<li> Hedging fees <br>
Generated based on number of days the protocol was open to risks due to the assets value.
<br>
File: /v1_profit_loss/views
<br>
<br>
<li> Smart Treasury - Mocked <br>
To maintain an 80/20 Cruize/USDC ratio by interacting with the open market to determine whether to selling or buy back cruize tokens.
<br>
File: /smart_treasury/views/
<br>
<br>
<li> Asset Historical data <br>
To generate an assets historical data with high and low price of asset 
for any given period. <br>
File: /tokens/views/
<br>
<br>

Example: 
Generating historical data on a day by day basis for the last 30 days 
will produce high and low value of the asset for each day. <br>
Similarly, data for a month by month basis for the last 6 months will produce high and low for each month in the last 6 months. 
