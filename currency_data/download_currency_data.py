import yfinance as yf
import pandas as pd
from datetime import datetime
from labels import currency, currency_tickers

currency_data = []

for idx, pair in enumerate(currency):
    ticker = currency_tickers[idx]
    data = yf.download(ticker, period="1y")

    data["Currency"] = pair
    currency_data.append(data)


combined_data_currency = pd.concat(currency_data)
combined_data_currency.to_csv(
    f"currency_data/combined_data_currency_{datetime.today().date()}.csv",
    index=True,
)
