import os

from openai import OpenAI
import pandas as pd
import json
from datetime import datetime
from currency_data.labels import currency
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

file_path = f"currency_data/currency_news_page_{datetime.today().date()}.csv"
df = pd.read_csv(file_path)
data_to_predict = df[["title", "description"]]

# Include information about currency pairs in the prompt
currency_pairs = currency  # Assuming you have a list of currency pairs
# Оголошуємо список для збереження результатів для кожної новини
all_predictions = []
rise_synonyms = [
    "up",
    "rise",
    "rose",
    "increased",
    "strengthened",
    "climbed",
    "advanced",
]  # Додайте інші можливі синоніми
fall_synonyms = [
    "fall",
    "down",
    "downward",
    "decreased",
    "weakened",
    "fell",
    "declined",
    "retreated",
]  # Додайте інші можливі синоніми

for _, row in data_to_predict.iterrows():
    title = row["title"]
    description = row["description"]

    # Формуємо текст запиту
    prompt = f"Аналіз новини: {title}. {description}. Валютні пари: {', '.join(currency_pairs)}."

    # Викликаємо OpenAI GPT API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
            {
                "role": "assistant",
                "content": "Provide predictions for currency pairs: will rise or will fall?",
            },
        ],
        max_tokens=300,  # Збільште кількість токенів за необхідності
    )

    # Обробляємо відповідь
    output_text = response.choices[0].message.content
    print(f"Output Text for {title}: {output_text}")

    predictions_dict = {}

    text_blocks = []
    pairs = currency_pairs

    for pair in pairs:
        start_index = output_text.find(f"{pair}:")
        end_index = output_text.find(
            f"{pairs[pairs.index(pair)+1]}:"
            if pairs.index(pair) < len(pairs) - 1
            else ""
        )

        if end_index == -1:
            end_index = None

        text_blocks.append(
            {"pair": pair, "block": output_text[start_index:end_index].strip()}
        )

    for block in text_blocks:
        pair_lower = block["pair"].lower()
        if pair_lower in block["block"].lower():
            for synonym in rise_synonyms:
                if synonym in block["block"]:
                    print(f"Rise detected for {block['pair']}")
                    predictions_dict[block["pair"]] = 1
                    break
            else:
                for synonym in fall_synonyms:
                    if synonym in block["block"]:
                        print(f"Fall detected for {block['pair']}")
                        predictions_dict[block["pair"]] = -1
                        break
                else:
                    print(f"No rise/fall detected for {block['pair']}")
                    predictions_dict[block["pair"]] = 0
        else:
            predictions_dict[block["pair"]] = 0

    # Додаємо результат для поточної новини до списку
    print(f"Title: {title}")
    print(f"Predictions Dict: {predictions_dict}")
    # Додаємо результат для поточної новини до списку
    all_predictions.append({title: predictions_dict})

# Зберігаємо список у JSON-файл
json_file_path = f"currency_data/openai_predictions_{datetime.today().date()}.json"
with open(json_file_path, "w") as json_file:
    json.dump(all_predictions, json_file)

print(f"Результати передбачень збережено у файлі {json_file_path}")
