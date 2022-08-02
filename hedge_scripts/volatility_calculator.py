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
    def get_sma_std_vol_of_returns(historical_data, rolling_number=14):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        sma_rolling = historical_data['returns'].rolling(rolling_number)
        vol = sma_rolling.std()
        historical_data['vol_sma_of_returns'] = vol
        vol_annualized = vol * np.sqrt(365)
        historical_data['vol_sma_of_returns_annualized'] = vol_annualized
        return {'vol_sma_of_returns_respect_to_periods': vol,
                'vol_sma_of_returns_annualized': vol_annualized}

    @staticmethod
    def get_ema_std_vol_of_returns(historical_data, com=0.5, min_periods=14):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        ema_of_com_in_periods = historical_data['returns'].ewm(com=com, min_periods=min_periods)
        vol = ema_of_com_in_periods.std()
        historical_data['vol_ema_of_returns'] = vol
        vol_annualized = vol * np.sqrt(365)
        historical_data['vol_ema_of_returns_annualized'] = vol_annualized
        return {'vol_ema_of_returns_respect_to_periods': vol,
                'vol_ema_of_returns_annualized': vol_annualized}

    @staticmethod
    def get_sma_std_vol_of_prices(historical_data, rolling_number=14):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        # historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        sma_rolling = historical_data['close'].rolling(rolling_number)
        vol = sma_rolling.std()
        historical_data['vol_sma_of_prices'] = vol
        vol_annualized = vol * np.sqrt(365)
        historical_data['vol_sma_prices_annualized'] = vol_annualized
        return {'vol_sma_of_prices_respect_to_periods': vol,
                'vol_sma_of_prices_annualized': vol_annualized}

    @staticmethod
    def get_ema_std_vol_of_prices(historical_data, com=0.5, min_periods=14):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        # historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        ema_of_com_in_periods = historical_data['close'].ewm(com=com, min_periods=min_periods)
        vol = ema_of_com_in_periods.std()
        historical_data['vol_ema_of_prices'] = vol
        vol_annualized = vol * np.sqrt(365)
        historical_data['vol_ema_of_prices_annualized'] = vol_annualized
        return {'vol_ema_of_prices_respect_to_periods': vol,
                'vol_ema_of_prices_annualized': vol_annualized}

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
    print([max(i.dropna()) for i in volatility_calc.get_sma_std_vol_of_prices(historical_data, 1*24).values()])
    print([max(i.dropna()) for i in volatility_calc.get_ema_std_vol_of_prices(historical_data, com=0.5, min_periods=1*24).values()])