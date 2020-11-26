
"""
# -- --------------------------------------------------------------------------------------------------- -- #
# -- project: A SHORT DESCRIPTION OF THE PROJECT                                                         -- #
# -- script: data.py : python script for data collection                                                 -- #
# -- author: YOUR GITHUB USER NAME                                                                       -- #
# -- license: GPL-3.0 License                                                                            -- #
# -- repository: YOUR REPOSITORY URL                                                                     -- #
# -- --------------------------------------------------------------------------------------------------- -- #
"""
import pandas as pd

def load_data_intraday(start: int = 2017, end: int = 2020):
    column_names = ["TimeStamp", "open", "high", "low", "close", "volume"]
    data = pd.DataFrame()
    for year in range(start, end + 1):
        file = 'files/ME_' + str(year) + '.csv'
        maindf = pd.read_csv(file,
                             header=1,
                             names=column_names,
                             parse_dates=["TimeStamp"],
                             index_col=["TimeStamp"])
        data = data.append(maindf)
    data.to_pickle("./EUR-USD-OPTIONS/future-historical-intraday.pkl")
    return data



def load_data_daily(start: int = 2017, end: int = 2020, freq: str = 'D'):
    column_names = ["TimeStamp", "open", "high", "low", "close", "volume"]
    data = pd.DataFrame()
    for year in range(start, end + 1):
        file = 'files/ME_' + str(year) + '.csv'
        maindf = pd.read_csv(file,
                             header=1,
                             names=column_names,
                             parse_dates=["TimeStamp"],
                             index_col=["TimeStamp"])

        sampled_df = maindf.resample(freq).agg({'open': 'first',
                                                'close': 'last',
                                                'high': 'max',
                                                'low': 'min',
                                                'volume': 'sum'})

        sampled_df = sampled_df[sampled_df.open > 0]
        if freq == 'D':
            sampled_df.index = sampled_df.index.date
        data = data.append(sampled_df)
    data.to_pickle("./EUR-USD-OPTIONS/future-historical-daily.pkl")
    return data

def load_options():
    file = './EUR-USD-OPTIONS/EUR-USD Dynamic Heding.xlsx'
    sheet = 'EURUSD-20181101-20201109'
    options = pd.read_excel(file, sheet)
    options.to_pickle("./EUR-USD-OPTIONS/options.pkl")
    return options
