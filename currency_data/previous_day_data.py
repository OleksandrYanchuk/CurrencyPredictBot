import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from labels import currency, currency_tickers

# Визначте дату попереднього дня
previous_day = datetime.today() - timedelta(days=1)
currency_data = []


# Змініть 'datetime.today().date()' на 'previous_day.date()' в зборі даних
for idx, pair in enumerate(currency):
    ticker = currency_tickers[idx]
    data = yf.download(ticker, period="previous_day")
    data.insert(0, "Data", previous_day.date())  # Додайте 'Data' з попереднім днем
    # Додаємо стовпець 'Currency' з назвою валютної пари
    data["Currency"] = pair
    currency_data.append(data)


# Об'єднуємо всі дані в один DataFrame
combined_data_currency = pd.concat(currency_data)


# Збережіть дані за акції та валютні пари за попередній день
combined_data_currency.to_csv(
    f"currency_data/previous_day_data_currency_{previous_day.date()}.csv",
    index=False,
)
