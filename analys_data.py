from datetime import datetime

import pandas as pd


# Завантаження даних
csv_filename = f"currency_data/combined_data_currency_{datetime.today().date()}.csv"

# Read CSV file, treating missing values as 0 in the sentiment column
currency_data = pd.read_csv(
    csv_filename,
    skiprows=[0],
    names=[
        "Data",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
        "Currency",
        "sentiment",
    ],
    dtype={
        "Open": float,
        "High": float,
        "Low": float,
        "Close": float,
        "Adj Close": float,
        "Volume": int,
        "sentiment": float,  # Change the dtype to float to handle potential NaN values
    },
    na_values={"sentiment": 0},  # Specify how NaN values are represented in the CSV
)
currency_data["Data"] = pd.to_datetime(currency_data["Data"])


# Розрахунок технічних індикаторів для кожної валютної пари
def calculate_technical_indicators(data):
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["SMA_200"] = data["Close"].rolling(window=200).mean()
    data["RSI"] = 100 - (
        100 / (1 + data["Close"].pct_change().rolling(window=14).mean())
    )
    data["MACD"] = (
        data["Close"].ewm(span=12, adjust=False).mean()
        - data["Close"].ewm(span=26, adjust=False).mean()
    )
    data["Signal_Line"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["Bollinger_Band_Upper"] = (
        data["Close"].rolling(window=20).mean()
        + 2 * data["Close"].rolling(window=20).std()
    )
    data["Bollinger_Band_Lower"] = (
        data["Close"].rolling(window=20).mean()
        - 2 * data["Close"].rolling(window=20).std()
    )
    return data


# Застосування функції до кожної валютної пари
currency_data = (
    currency_data.groupby("Currency")
    .apply(calculate_technical_indicators)
    .reset_index(drop=True)
)

# Вибірка необхідних стовпців для збереження
selected_columns = [
    "Data",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Currency",
    "sentiment",
    "SMA_50",
    "SMA_200",
    "RSI",
    "MACD",
    "Signal_Line",
    "Bollinger_Band_Upper",
    "Bollinger_Band_Lower",
]

# Збереження оновленого DataFrame без перших двох стовпців
currency_data[selected_columns].to_csv(
    f"currency_data/currency_data_with_all_indicators_{datetime.today().date()}.csv",
    index=False,
)
