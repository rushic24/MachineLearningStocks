import re
import json
import csv
from io import StringIO
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
from datetime import datetime
from utils import data_string_to_float
from tqdm import tqdm
import numpy as np
from .constants import url_stats, url_profile, url_financials, features, statspath


# the stock I want to scrape
# stock = 'F'

def getFundaMentalsForTicker(stock='F'):
    value_list = None
    summary = None
    statistics = None
    try:
        response = requests.get(url_financials.format(stock, stock))

        soup = BeautifulSoup(response.text, 'html.parser')

        pattern = re.compile(r'\s--\sData\s--\s')
        script_data = soup.find('script', text=pattern).contents[0]

        # find the starting position of the json string
        start = script_data.find("context")-2

        # slice the json string
        json_data = json.loads(script_data[start:-12])

        ## Profile data
        response = requests.get(url_profile.format(stock, stock))
        soup = BeautifulSoup(response.text, 'html.parser')
        pattern = re.compile(r'\s--\sData\s--\s')
        script_data = soup.find('script', text=pattern).contents[0]
        start = script_data.find("context")-2
        json_data = json.loads(script_data[start:-12])

        summary = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']


        ## Statistics
        response = requests.get(url_stats.format(stock, stock))
        soup = BeautifulSoup(response.text, 'html.parser')
        pattern = re.compile(r'\s--\sData\s--\s')
        script_data = soup.find('script', text=pattern).contents[0]
        start = script_data.find("context")-2
        json_data = json.loads(script_data[start:-12])

        statistics = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['defaultKeyStatistics']

        # print(statistics['shortPercentOfFloat'].get('raw', 'N/A'))
        value_list = [
            #marketcap
            summary['summaryDetail']['marketCap'].get('raw', 'N/A'),
            #enterprise value
            statistics['enterpriseValue'].get('raw', 'N/A'),
            #forwarepe
            summary['summaryDetail']['forwardPE'].get('raw', 'N/A'), 
            #pegratio
            statistics['pegRatio'].get('raw', 'N/A'),
            summary['summaryDetail']['priceToSalesTrailing12Months'].get('raw', 'N/A'),
            statistics['priceToBook'].get('raw', 'N/A'),
            statistics['enterpriseToRevenue'].get('raw', 'N/A'),
            statistics['enterpriseToEbitda'].get('raw', 'N/A'),
            statistics['profitMargins'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['operatingMargins'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['returnOnAssets'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['returnOnEquity'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['totalRevenue'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['revenuePerShare'].get('raw', 'N/A'),
            statistics['revenueQuarterlyGrowth'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['grossProfits'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['ebitda'].get('raw', 'N/A'),
            statistics['netIncomeToCommon'].get('raw', 'N/A'),
            statistics['earningsQuarterlyGrowth'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['totalCash'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['totalCashPerShare'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['totalDebt'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['debtToEquity'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['currentRatio'].get('raw', 'N/A'),
            statistics['bookValue'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['operatingCashflow'].get('raw', 'N/A'),
            json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']['freeCashflow'].get('raw', 'N/A'),
            summary['summaryDetail']['beta'].get('raw', 'N/A'),
            summary['summaryDetail']['fiftyDayAverage'].get('raw', 'N/A'),
            summary['summaryDetail']['twoHundredDayAverage'].get('raw', 'N/A'),
            summary['summaryDetail']['averageVolume'].get('raw', 'N/A'),
            statistics['sharesOutstanding'].get('raw', 'N/A'),
            statistics['floatShares'].get('raw', 'N/A'),
            statistics['heldPercentInsiders'].get('raw', 'N/A'),
            statistics['heldPercentInstitutions'].get('raw', 'N/A'),
            statistics['sharesShort'].get('raw', 'N/A'),
            statistics['shortPercentOfFloat'].get('raw', 'N/A'),
            statistics['sharesShortPriorMonth'].get('raw', 'N/A'),
        ]
    except KeyError:
        pass
    except TypeError:
        pass
    return value_list



def forward():
    # Creating an empty dataframe which we will later fill. In addition to the features, we need some index variables
    # (date, unix timestamp, ticker), and of course the dependent variables (prices).
    df_columns = [
        "Date",
        "Unix",
        "Ticker",
        "Price",
        "stock_p_change",
        "SP500",
        "SP500_p_change",
    ] + features

    df = pd.DataFrame(columns=df_columns)

    # The tickers whose data is to be parsed.
    stock_list = [x[0] for x in os.walk(statspath)]
    stock_list = stock_list[1:]

    for i in tqdm(stock_list, desc="Parsing progress:", unit="tickers"):
        ticker = i.split(statspath)[1].upper()
        print(f'Fetching fundamental for {ticker}')
        value_list = getFundaMentalsForTicker(ticker)
        #print(len(features))
        #print(len(value_list))
        if value_list:
            new_df_row = [0, 0, ticker, 0, 0, 0, 0] + value_list
            df = df.append(dict(zip(df_columns, new_df_row)), ignore_index=True)
        else:
            print(f'Failed to fetch {ticker}')
    return df.replace("N/A", np.nan)


if __name__ == "__main__":
    current_df = forward()
    current_df.to_csv("jsontest.csv", index=False)
'''

value_list = []
for variable in features:
    try:
        # Basically, look for the first number present after we an occurence of the variable
        value = 
        value_list.append(data_string_to_float(value))

    # The data may not be present. Process accordingly.
    except AttributeError:
        value_list.append("N/A")
        # print(ticker, variable)


'''