import os

import pandas as pd
import json
from datetime import datetime

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

# Fill NaN values in the sentiment column with 0
currency_data["sentiment"].fillna(0, inplace=True)

# Convert the sentiment column to int
currency_data["sentiment"] = currency_data["sentiment"].astype(int)

current_date = datetime.today().date()

json_filename = f"currency_data/openai_predictions_{datetime.today().date()}.json"

if os.path.exists(json_filename):
    with open(json_filename, "r") as json_file:
        news_predictions = json.load(json_file)

    for news in news_predictions:
        for key, value in news.items():
            for currencies, sentimental in value.items():
                date_filter = currency_data["Data"].dt.date == current_date
                currency_filter = currency_data["Currency"] == currencies
                matching_rows = currency_data[date_filter & currency_filter]

                if not matching_rows.empty:
                    # Get the existing sentiment value
                    existing_sentiment = matching_rows["sentiment"].values[0]

                    # Apply constraints on sentiment value
                    new_sentiment = max(-1, min(existing_sentiment + sentimental, 1))

                    currency_data.loc[
                        date_filter & currency_filter, "sentiment"
                    ] = new_sentiment
                    print(
                        f"Sentiment for {currencies} on {current_date}: {new_sentiment}"
                    )
                else:
                    print(f"No data found for {currencies} on {current_date}")
else:
    # If the predictions file does not exist, reset the "sentiment" column to zero
    currency_data["sentiment"] = 0
    print("No predictions file found. Resetting sentiment column to zero.")

# Save the updated DataFrame back to the CSV file
currency_data.to_csv(csv_filename, index=False)
