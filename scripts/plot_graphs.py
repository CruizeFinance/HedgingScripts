class PlotGraphs():

    def plot(self):

        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        import datetime

        # dummy data (Days)
        dates_d = pd.date_range('2022-01-01', '2023-01-31', freq='D')

        # Give random numbers to each month
        df_year = pd.DataFrame(np.random.randint(100, 200, (dates_d.shape[0], 1)), columns=['Data'])
        df_year.index = dates_d #set index

        # Assign integer number to each month. 1..12
        pt = pd.pivot_table(df_year, index=df_year.index.month, columns=df_year.index.year, aggfunc='sum')
        # pt.columns = pt.columns.droplevel() # remove the double header (0) as pivot creates a multiindex.

        ax = plt.figure().add_subplot(111)
        # ax.plot(pt) # No need for this code cause it simply puts the pt df on the graph to show how data will look.

        # Set month names on X-Axis
        month_ticklabels = []
        # month_ticklabels = [datetime.date(2022, item, 1).strftime('%b') for item in pt.index]
        for item in pt.index:
            # print(item)
            year = datetime.date(2022, item, 1).strftime('%Y')
            month = datetime.date(2022, item, 1).strftime('%b')
            # print(month + ', '+ year)
            month_label = month + ', '+ year
            month_ticklabels.append(month_label)

        ax.set_xticks(np.arange(1, 13))
        ax.set_xticklabels(month_ticklabels, rotation=45) #add monthlabels to the xaxis
        # -----
        ax.legend(pt.columns.tolist(), loc='center left', bbox_to_anchor=(1, .5)) #add the column names as legend.
        plt.tight_layout(rect=[0, 0, 0.85, 1])

        # Set APY on Y-Axis
        apy_tick_labels = [2, 5, 7, 9, 11, 13, 15] # in %age
        plt.yticks(apy_tick_labels)

        # Assign data to the grap
        # example_data_apy_generated = pd.DataFrame([155, 1000, 2500, 3000, 4000, 155, 1000, 2500, 3000, 4000, 155, 1000])
        # ax.plot(example_data_apy_generated)
        # ------------

        # Add horizontal grid lines
        plt.grid(axis='y')

        plt.show()

if __name__ == '__main__':
    pg = PlotGraphs()
    pg.plot()