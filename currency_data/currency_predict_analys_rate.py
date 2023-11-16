import glob
import json
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from math import sqrt


def analysis_function(previous_day_data, predicted_prices):
    # Обчисліть різні метрики для порівняння фактичних та передбачених цін
    rmse = sqrt(mean_squared_error(previous_day_data["Close"], predicted_prices))
    mae = mean_absolute_error(previous_day_data["Close"], predicted_prices)

    # Округліть кожен елемент списку передбачених цін
    predicted_prices = [round(price, 6) for price in predicted_prices]

    actual_change = [
        (round((actual * 100), 6) / round(open_price, 6)) - 100
        for actual, open_price in zip(
            previous_day_data["Close"], previous_day_data["Open"]
        )
    ]
    predict_change = [
        (round((predicted * 100), 6) / round(open_price, 6)) - 100
        for predicted, open_price in zip(predicted_prices, previous_day_data["Open"])
    ]

    actual_change = [round(change, 2) for change in actual_change]
    predict_change = [round(change, 2) for change in predict_change]

    return {
        "RMSE": rmse,
        "MAE": mae,
        "actual_change": actual_change,
        "predict_change": predict_change,
    }


# Отримайте список файлів з фактичними цінами закриття та передбаченнями
previous_day_data_files = glob.glob("currency_data/previous_day_data_currency_*.csv")
prediction_files = glob.glob("currency_data/currency_predictions_*.json")

# Отримайте список унікальних дат з назв файлів
dates_previous_day_data = [
    file.split("_")[-1].split(".")[0] for file in previous_day_data_files
]
dates_predictions = [file.split("_")[-1].split(".")[0] for file in prediction_files]

# Знайдіть спільні дати для аналізу
common_dates = set(dates_previous_day_data) & set(dates_predictions)

results = {}
for date in common_dates:
    # Отримайте файли з фактичними цінами закриття та передбаченнями для поточної дати
    previous_day_data_file = f"currency_data/previous_day_data_currency_{date}.csv"
    prediction_file = f"currency_data/currency_predictions_{date}.json"

    # Завантажте фактичні ціни закриття
    previous_day_data = pd.read_csv(previous_day_data_file)

    # Заванажте передбачення
    with open(prediction_file, "r") as json_file:
        predictions = json.load(json_file)

    # Виконайте аналіз для кожної валютної пари окремо
    for currency_pair, predicted_prices in predictions.items():
        # Виберіть дані для обраної валютної пари
        currency_data = previous_day_data[
            previous_day_data["Currency"] == currency_pair
        ]

        # Виконайте аналіз для цієї валютної пари
        analysis_result = analysis_function(currency_data, predicted_prices)

        # Створіть рядковий ключ, що містить інформацію про дату та валютну пару
        result_key = f"{currency_pair}"

        # Збережіть результати для кожної валютної пари з використанням рядкового ключа
        results[result_key] = analysis_result

# Збережіть результати в JSON-файл
with open("currency_data/currency_analysis_results.json", "w") as json_file:
    json.dump(results, json_file, indent=4)

print("Результати аналізу збережено у файлі 'currency_analysis_results.json'.")
