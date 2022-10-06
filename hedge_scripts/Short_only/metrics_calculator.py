import math
import random
import numpy as np
from scipy.stats import norm
import pandas as pd
import matplotlib.pyplot as plt

import interval


class MetricsCalculator(object):

    def ATR(self, df, n):
        "function to calculate True Range and Average True Range"
        df = df.copy()

        df['H-L'] = abs(df['high'] - df['low'])
        df['H-PO'] = abs(df['high'] - df['open'].shift(1))
        df['L-PO'] = abs(df['low'] - df['open'].shift(1))

        df['TR'] = df[['H-L', 'H-PO', 'L-PO']].max(axis=1, skipna=False)
        df['ATR_SMA'] = df['TR'].rolling(n).mean()
        df['ATR_EMA'] = df['TR'].ewm(alpha=0.8, adjust=False).mean()

        df2 = df.drop(['H-L', 'H-PO', 'L-PO'], axis=1)
        return df2

    def CES(self, df, n, m):
        df2 = self.ATR(df, n)
        df2['CES_SMA_' + str(n) + '_' + str(m)] = [None] * len(df2)
        df2['CES_EMA_' + str(n) + '_' + str(m)] = [None] * len(df2)
        for i in range(n, len(df2)):
            df2['CES_SMA_' + str(n) + '_' + str(m)][i] = df2[-n:]['low'].min() + m * df2['ATR_SMA'][i]
            df2['CES_EMA_' + str(n) + '_' + str(m)][i] = df2[-n:]['low'].min() + m * df2['ATR_EMA'][i]
        return df2

    def CES_test(self, df_with_ces, n, m):
        pnl = 0
        i = 0
        while i < len(df_with_ces):
            current_price = df_with_ces['close'][i]
            # search for index st price>CES
            j = 0
            if isinstance(df_with_ces['CES_EMA_' + str(n) + '_' + str(m)][i+j], type(None)):
                j += 1
            else:
                while(df_with_ces['close'][i+j] < df_with_ces['CES_EMA_' + str(n) + '_' + str(m)][i+j]):
                    if i+j == len(df_with_ces)-1:
                        return current_price - df_with_ces['close'][i+j]
                    j += 1
            pnl += current_price - df_with_ces['close'][i+j]
            i = i+j
        return pnl

if __name__ == '__main__':
    metric_calculator = MetricsCalculator()
    metric_calculator.df = pd.read_csv("/files/ETHUSDC-1m-data_since_1 Sep 2019.csv")[-1000:]
    # # assign data to stgy instance + define index as dates
    # df = pd.DataFrame(historical_data["close"], columns=['close'])
    timestamp = pd.to_datetime(metric_calculator.df['timestamp'])
    metric_calculator.df.index = timestamp
    metric_calculator.df = metric_calculator.df.drop(['timestamp'], axis=1)
    df2 = metric_calculator.CES(metric_calculator.df, 30, 3)
    # print(df2[['close', 'CES_SMA_30_3','CES_EMA_30_3', 'ATR_EMA', 'ATR_SMA']])
    # print(metric_calculator.CES_test(df2, 30, 3))
    # print((df2['CES_SMA_30_3']/df2['close']-1)*100)
    # print((df2['CES_EMA_30_3']/df2['close']-1)*100)
    fig, axs = plt.subplots(1, 1, figsize=(21, 7))
    axs.plot(df2['close'], color='tab:blue', label='market price')
    axs.plot(df2['CES_SMA_30_3'], color='tab:red', label='CES_SMA_30_3')
    # axs.plot(df2['CES_EMA_30_3'], color='green', label='CES_EMA_30_3')
    axs.grid()
    axs.legend(loc='lower left')
    plt.show()

