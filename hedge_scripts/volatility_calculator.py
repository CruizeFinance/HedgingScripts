import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm


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
    def get_ema_std_vol_of_returns(hist_data, alpha, min_periods):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        # historical_data = hist_data[-2*30*24:].copy()
        historical_data = hist_data.copy()
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = abs(log_returns.dropna())
        ema_of_com_in_periods = log_returns.ewm(alpha=alpha, min_periods=min_periods)
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
    def get_ema_std_vol_of_prices(historical_data, alpha, min_periods):
        # Rolling Volatility (annualized assuming 365 trading days)
        # 2 week
        # historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        ema_of_com_in_periods = historical_data['close'].ewm(alpha=alpha, min_periods=min_periods)
        ema = ema_of_com_in_periods.mean()
        vol = ema_of_com_in_periods.std()
        historical_data['vol_ema_of_prices'] = vol
        vol_annualized = vol * np.sqrt(365)
        historical_data['vol_ema_of_prices_annualized'] = vol_annualized
        return {'vol_ema_of_prices_respect_to_periods': vol,
                'vol_ema_of_prices_annualized': vol_annualized,
                'ema':ema}

    @staticmethod
    def get_bollinger_bands(historical_data, sma_length=20):
        historical_data['returns'] = np.around(historical_data['close'].pct_change().dropna(), 3)
        historical_data['sma'] = historical_data['returns'].rolling(sma_length).mean()
        # Upper band
        historical_data['b_upper'] = historical_data['sma20'] + 2 * historical_data['sma20'].rolling(20).std()
        # Lower band
        historical_data['b_lower'] = historical_data['sma20'] - 2 * historical_data['sma20'].rolling(20).std()

        return historical_data


    # ARCH
    @staticmethod
    def get_arch(historical_data, p, o, q):
        ####################################################################
        # ARCH the baseline volality of the Bitcoin log returns
        ####################################################################
        from arch import arch_model
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = abs(log_returns.dropna())
        am = arch_model(log_returns, p=p, o=o, q=q)
        res = am.fit(update_freq=5)
        # print(res.summary())
        # fig = res.plot(annualize="D")
        df = pd.DataFrame({'Vol: abs(log_returns)': log_returns[10:], 'ARCH(1)': res.conditional_volatility[10:]})
        # df = pd.DataFrame({'Vol: log_returns': log_returns[10:], 'ARCH(1)': res.conditional_volatility[10:]})
        subplot = df.plot(title='ARCH(1) Model Applied to Vol')
        plt.show()
        return list(res.conditional_volatility)[-1]

    # GARCH
    @staticmethod
    def get_garch(historical_data):
        ####################################################################
        # GARCH the baseline volality of the Bitcoin log returns
        ####################################################################
        from arch import arch_model
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = abs(log_returns.dropna())
        am = arch_model(log_returns)  # GARCH MODEL p=1 , q=1
        res = am.fit(update_freq=5)
        # print(res.summary())
        # fig = res.plot(annualize="D")
        df = pd.DataFrame({'Vol: abs(log_returns)': log_returns[10:], 'GARCH(1,1)': res.conditional_volatility[10:]})
        # df = pd.DataFrame({'Vol: log_returns': log_returns[10:], 'GARCH(1,1)': res.conditional_volatility[10:]})
        subplot = df.plot(title='GARCH(1,1) Model Applied to Vol')
        plt.show()

    # EMWA
    @staticmethod
    def rho_cal(historical_data):
        import scipy
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = abs(log_returns.dropna())
        rho_hat = scipy.stats.pearsonr(log_returns - np.mean(log_returns), np.sign(
            log_returns - np.mean(log_returns)))  # rho_hat[0]:Pearson correlation , rho_hat[1]:two-tailed p-value
        return rho_hat[0]

    def get_emwa(self, historical_data, window):
        cut_t = window
        alpha = np.arange(0.01, 0.95, 0.01)
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = abs(log_returns.dropna())
        t = len(log_returns)

        rho = self.rho_cal(historical_data)  # calculate sample sign correlation
        # print(rho)
        vol = abs(log_returns - np.mean(log_returns)) / rho  # calculate observed volatility
        # print(vol)
        MSE_alpha = np.zeros(len(alpha))
        sn = np.zeros(len(alpha))  # volatility
        for a in range(len(alpha)):
            s = np.mean(vol[0:cut_t])  # initial smoothed statistic
            error = np.zeros(t)
            for i in range(1, t):
                error[i] = vol[i] - s
                s = alpha[a] * vol[i] + (1 - alpha[a]) * s
            MSE_alpha[a] = np.mean(
                (error[(len(error) - cut_t):(len(error))]) ** 2)  # forecast error sum of squares (FESS)
            sn[a] = s
        vol_forecast = sn[[i for i, j in enumerate(MSE_alpha) if j == min(MSE_alpha)]]  # which min
        RMSE = np.sqrt(min(MSE_alpha))

        return vol_forecast

    @staticmethod
    def get_arima(historical_data):
        from statsmodels.tsa.arima_model import ARIMA
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = log_returns.dropna()
        np.var(log_returns.iloc[1:])  # variance of SPY_vol
        y = abs(log_returns.iloc[1:])
        model = ARIMA(y, order=(1, 0, 1))  # ARMA(1,1) model
        model_fit = model.fit(disp=0)
        print(model_fit.summary())

    @staticmethod
    def plot_log_returns(historical_data, window, bins):
        """
        We assume returns are normally distributed
        """

        historical = historical_data.copy()
        pct_change = historical['close'].pct_change(window).fillna(method='bfill')
        return_usd = historical['close'] - historical['close'].shift(window)
        log_returns = np.log(historical['close']) - np.log(historical['close'].shift(window))
        # historical['pct_change'] = pct_change
        # historical['log_returns'] = log_returns

        # x = np.linspace(pct_change.min(), 1, 100)
        # mean = np.mean(pct_change)
        # std = np.std(pct_change)
        # norm_dist = norm.pdf(x, mean, std)
        fig, axs = plt.subplots(2, 1, figsize=(21, 7))
        fig.suptitle("Log returns analysis")
        # log_returns.hist(bins=50, ax=axs)
        # pct_change.hist(bins=50, ax=axs)
        axs[0].hist(log_returns, bins=bins)
        axs[0].set_ylabel('Samples')
        axs[1].set_ylabel('Log Returns')
        axs[0].set_title('Distribution')
        axs[1].set_title('Volatility')
        axs[1].plot(return_usd, color='tab:blue', label='Returns dist')
        # To check if its normally distributed + understate the likelihood of returns beyond -2/+2 quantiles
        # import scipy.stats as stats
        # stats.probplot(historical['returns'], dist='norm', plot=axs)
        # axs.grid()
        plt.show()
        # print(historical.describe())

    @staticmethod
    def plot_ACF(historical_data):
        # To check whether each daily return is uncorrelated with the pervious days.
        import statsmodels.api as sm
        import statsmodels.tsa.api as smt
        historical = historical_data.copy()
        pct_change = historical['close'].pct_change().fillna(method='bfill')
        log_returns = np.log(historical['close']) - np.log(historical['close'].shift(1))
        log_returns = log_returns.dropna()
        fig, ax = plt.subplots(figsize=(14, 10))
        smt.graphics.plot_acf(log_returns, lags=25, alpha=0.05, ax=ax)
        plt.show()
        
    @staticmethod
    def find_distribution(historical_data):
        from distfit import distfit
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(1))
        log_returns = log_returns.dropna()
        dist_names = ["weibull_min", "norm", "weibull_max", "beta",
        "invgauss", "uniform", "gamma", "expon",
        "lognorm", "pearson3","triang"]

        # Initialize distfit
        dist = distfit()

        # Determine best-fitting probability distribution for data
        dist.fit_transform(log_returns)
        #recalling that the lowest RSS will provide the best fit
        print(dist.summary[['distr', 'score']])
        # Plot results

        fig,axs = plt.subplots(2, 1, figsize=(21, 7))
        # fig.suptitle("Log returns analysis")
        dist.plot(ax=axs[0])
        axs[1].plot(dist.summary.distr, dist.summary.score)
        plt.tight_layout()  # makes that labels etc. fit nicely
        plt.show()

    def calc_var(self, historical_data):
        # compute returns
        import math
        data = historical_data['close']
        returns_log = [math.log(data[i + 1] / data[i], 10) for i in range(0, len(data) - 1)]
        log_returns = np.log(historical_data['close']) - np.log(historical_data['close'].shift(10))
        log_returns = log_returns.dropna()
        # calculate std_21 for returns
        std_21_log = [np.std(returns_log[t - 21:t]) for t in range(21, len(returns_log))]

        # std_42=[np.std(returns[t-42:t]) for t in range(42,len(returns))]

        # We calculate \mu_10D,t
        mu_log = np.mean(returns_log)
        mu_10D_log = mu_log * 10

        # calculate VaR10D,t. I show three differents ways of doing it.
        # Confidence
        Confidence = 0.99
        # Remember that norm.ppf(c)=\phi^{-1}(c) and norm.pdf(c)=\phi(c)
        Factor = norm.ppf(
            1 - Confidence)
        # i.e. Factor = \phi^{-1}(0.01) i.e. The method norm.ppf() takes a percentage
        # and returns a standard deviation multiplier for what value that percentage occurs at.
        # Using the \mu_10D,t term
        VaR_21_log_with_mu = [mu_10D_log + Factor * std_21_log[t] * math.sqrt(10) for t in range(0, len(std_21_log))]

if __name__ == "__main__":
    # i=4
    # import json
    # import stgyapp
    #
    # with open("/home/agustin/Git-Repos/HedgingScripts/files/StgyApp_config.json") as json_file:
    #     config = json.load(json_file)
    # # aave.Aave(config["initial_parameters"]["aave"])
    # # Initialize stgyApp
    # stgy = stgyapp.StgyApp(config)
    # symbol = 'ETHUSDC'
    # freq = '1d'
    # initial_date = "1 Jan 2020"
    # stgy.call_binance_data_loader(symbol=symbol, freq=freq,
    #                               initial_date=initial_date, save=True)
    # historical_data = pd.DataFrame(stgy.historical_data)

    historical_data = pd.read_csv("/home/agustin/Git-Repos/HedgingScripts/files/ETHUSDC-1d-data.csv")
    # historical_data.index = historical_data['timestamp']
    from datetime import datetime
    # historical_data['timestamp'].dt.strftime('%Y-%m-%d')
    # plt.plot(historical_data['timestamp'], historical_data['close'])
    # print(type(historical_data.index[0]))
    # plt.plot(historical_data['close'])
    # plt.show()
    volatility_calc = VolatilityCalculator()
    volatility_calc.plot_log_returns(historical_data, window=15, bins=30)
    # arch = volatility_calc.get_arch(historical_data, 1, 0, 0)
    # garch = volatility_calc.get_arch(historical_data, 1, 0, 1)
    # emwa = volatility_calc.get_emwa(historical_data, window=50)[0]
    # ema = volatility_calc.get_ema_std_vol_of_returns(
    #     historical_data, alpha=0.8, min_periods=14)['vol_ema_of_returns_annualized'].dropna()
    # sma = volatility_calc.get_sma_std_vol_of_returns(
    #     historical_data, rolling_number=14)['vol_sma_of_returns_annualized'].dropna()
    # print(sma.iloc[[-30, -7, -1]])
    # print(ema.iloc[[-30, -7, -1]])


    # ema vs sma + comparison with messari and t3
    volatility_calc.historical_data = pd.DataFrame(historical_data["close"], columns=['close'])
    timestamp = pd.to_datetime(historical_data['timestamp'])
    # stgy.historical_data.column = ['close']
    # ewm = historical_data['close'].ewm(alpha=alpha, min_periods=min_periods)

    # EMA and SMA of prices
    ewm_prices = volatility_calc.historical_data['close'].ewm(span=30)
    rolling_prices = volatility_calc.historical_data['close'].rolling(30)
    std_prices = ewm_prices.std()
    ema_prices = ewm_prices.mean()
    sma_prices = rolling_prices.mean()
    volatility_calc.historical_data['std_prices'] = std_prices
    volatility_calc.historical_data['ema_prices'] = ema_prices
    volatility_calc.historical_data['sma_prices'] = sma_prices

    # EMA and SMA of returns
    import numpy as np

    returns = np.around(volatility_calc.historical_data['close'].pct_change().dropna(), 3)
    volatility_calc.historical_data['returns'] = returns
    ewm_returns = volatility_calc.historical_data['returns'].ewm(span=365)
    # ewm_returns = volatility_calc.historical_data['returns'].ewm(alpha=0.5)
    rolling_returns = volatility_calc.historical_data['returns'].rolling(365)
    std_returns = ewm_returns.std()
    ema_returns = ewm_returns.mean()
    sma_returns = rolling_returns.mean()
    volatility_calc.historical_data['std_returns'] = std_returns
    volatility_calc.historical_data['ema_returns'] = ema_returns
    volatility_calc.historical_data['sma_returns'] = ema_returns

    # EMA and SMA of log returns
    log_returns = np.log(volatility_calc.historical_data['close']) - np.log(volatility_calc.historical_data['close'].shift(1))
    volatility_calc.historical_data['log_returns'] = log_returns
    # ewm_log_returns = volatility_calc.historical_data['log_returns'].ewm(span=15)
    ewm_log_returns = volatility_calc.historical_data['log_returns'][-30:].ewm(alpha=0.8, adjust=False)
    rolling_log_returns = volatility_calc.historical_data['log_returns'].rolling(365)
    std_log_returns = ewm_log_returns.std()
    ema_log_returns = ewm_log_returns.mean()
    sma_log_returns = rolling_log_returns.mean()
    volatility_calc.historical_data['std_log_returns'] = std_log_returns
    volatility_calc.historical_data['ema_log_returns'] = ema_log_returns
    volatility_calc.historical_data['sma_log_returns'] = sma_log_returns
    volatility_calc.historical_data.index = timestamp

    # N = 3*12*30
    # ewm_returns = volatility_calc.historical_data['returns'][-N:].ewm(alpha=0.8, adjust=False)
    # ewm_log_returns = volatility_calc.historical_data['log_returns'][-N:].ewm(alpha=0.8, adjust=False)
    # rolling_returns = volatility_calc.historical_data['returns'][-N:].rolling(window=14)
    # rolling_log_returns = volatility_calc.historical_data['log_returns'][-N:].rolling(window=14)
    # std_ema_returns = round(ewm_returns.std().mean() * 100 * np.sqrt(365), 3)
    # std_ema_log_returns = round(ewm_log_returns.std().mean() * 100 * np.sqrt(365), 3)
    # std_sma_returns = round(rolling_returns.std().dropna().mean() * 100 * np.sqrt(365), 3)
    # std_sma_log_returns = round(rolling_log_returns.std().dropna().mean() * 100 * np.sqrt(365), 3)
    # print('ema_returns_' + str(N) + ': ' + str(std_ema_returns) + '%')
    # print('ema_log_returns_' + str(N) + ': ' + str(std_ema_log_returns) + '%')
    # print('sma_returns_' + str(N) + ': ' + str(std_sma_returns) + '%')
    # print('sma_log_returns_' + str(N) + ': ' + str(std_sma_log_returns) + '%')
    # plt.plot(rolling_returns.std().dropna()*100*np.sqrt(365), label='sma std')
    # plt.plot(ewm_returns.std() * 100 * np.sqrt(365), label='ema std')
    # plt.legend()
    # plt.show()
    # plots
    # close vs ema prices vs sma prices
    # plt.plot(volatility_calc.historical_data['close'], label='eth')
    # plt.plot(volatility_calc.historical_data['ema_prices'], label='ema_30')
    # plt.plot(volatility_calc.historical_data['sma_prices'], label='sma_30')

    # ema returns vs sma returns
    # plt.plot(volatility_calc.historical_data['ema_returns'], label='ema_30_returns')
    # plt.plot(volatility_calc.historical_data['sma_returns'], label='sma_30_returns')
    #
    # # ema log returns vs sma log returns
    # plt.plot(volatility_calc.historical_data['ema_log_returns'], label='ema_30_log_returns')
    # plt.plot(volatility_calc.historical_data['sma_log_returns'], label='sma_30_log_returns')
    # plt.legend()
    # # plt.plot(volatility_calc.historical_data['std_log_returns'])
    # plt.show()