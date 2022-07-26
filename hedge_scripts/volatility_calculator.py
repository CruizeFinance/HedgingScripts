import numpy as np
import pandas as pd


class VolatilityCalculator(object):

    @staticmethod
    def get_std_vol(historical_data):
        """
        historical data has to be a df OHLC data
        """
        returns = np.around(historical_data['close'].pct_change().dropna(), 3)
        mu = np.mean(returns)
        sigma = np.std(returns)
        sigma_anualized = sigma * np.sqrt(365)

        return sigma_anualized

    @staticmethod
    def get_atr(historical_data, atr_length):
        "function to calculate True Range and Average True Range"

        historical_data['H-L'] = abs(historical_data['High'] - historical_data['Low'])
        historical_data['H-PO'] = abs(historical_data['High'] - historical_data['Open'].shift(1))
        historical_data['L-PO'] = abs(historical_data['Low'] - historical_data['Open'].shift(1))

        historical_data['TR'] = historical_data[['H-L', 'H-PO', 'L-PO']].max(axis=1, skipna=False)
        historical_data['ATR'] = historical_data['TR'].rolling(atr_length).mean()

        df2 = historical_data.drop(['H-L', 'H-PO', 'L-PO'], axis=1)
        return df2

    @staticmethod
    def get_rolling_volatility(historical_data, rolling_number=14):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        vol = historical_data['returns'].rolling(rolling_number).std()
        vol_annualized = vol * np.sqrt(365)
        return vol_annualized

    @staticmethod
    def get_bollinger_bands(historical_data, sma_length = 20):
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        historical_data['sma'] = historical_data['returns'].rolling(sma_length).mean()
        # Upper band
        historical_data['b_upper'] = historical_data['sma20'] + 2 * historical_data['sma20'].rolling(20).std()
        # Lower band
        historical_data['b_lower'] = historical_data['sma20'] - 2 * historical_data['sma20'].rolling(20).std()

        return historical_data

    # def get_implied_volatility(self, historical_data):

if __name__ == "__main__":
    historical_data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/stgy.historical_data.csv")
    volatility_calc = VolatilityCalculator()
    print(np.mean(volatility_calc.get_rolling_volatility(historical_data, 24)/np.sqrt(365)))