import asyncio
import logging
import os
import json
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from currency_data.labels import currency

from dotenv import load_dotenv


load_dotenv()

json_file_path = "user_data.json"


# Функція для завантаження даних з JSON-файлу
def load_currency_data():
    file_name = f"currency_data/currency_predictions_{datetime.today().date()}.json"
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data


def load_currency_data_analys():
    file_name = f"currency_data/currency_analysis_results.json"
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data


API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
button_currency = KeyboardButton("Currency")
button_currency_analyse = KeyboardButton("Analyse_currency")

markup.add(button_currency, button_currency_analyse)

items_per_page = 15

current_page = 1

previous_day = datetime.today().date() - timedelta(days=1)

currency_pairs = currency
global user_choice
user_choice = None

currency_keyboard = InlineKeyboardMarkup()
for pair in currency_pairs:
    currency_keyboard.add(InlineKeyboardButton(text=pair, callback_data=f"pair_{pair}"))


# Function to read data from the JSON file
def read_json():
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []


# Function to write data to the JSON file
def write_json(data):
    with open(json_file_path, "w") as file:
        json.dump(data, file)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    data = read_json()

    # Add the new user_id to the data
    data.append({f"user_id_{user_id}": user_id})

    # Write the updated data back to the JSON file
    write_json(data)

    await message.answer(
        "Привіт! Це твій бот. Вибери, що ти хочеш передбачити:", reply_markup=markup
    )


@dp.message_handler(lambda message: message.text in ["Currency", "Stocks"])
async def process_user_choice(message: types.Message):
    global user_choice
    user_choice = message.text

    if user_choice == "Currency":
        await message.answer("Обери валютну пару:", reply_markup=currency_keyboard)
    elif user_choice == "Analyse_currency":
        await show_currency_analys_page(message, current_page)


@dp.callback_query_handler(lambda query: query.data.startswith("pair_"))
async def process_currency_choice(query: types.CallbackQuery):
    selected_pair = query.data.replace("pair_", "")

    # Завантажте дані з JSON-файлу
    currency_data = load_currency_data()

    # Отримайте ціну закриття для обраної валютної пари
    if selected_pair in currency_data:
        closing_price = currency_data[selected_pair]
        message_text = f"Орієнтовна ціна закриття на {datetime.today().date()} валютної пари ({selected_pair}): {closing_price}"
    else:
        message_text = f"Дані для валютної пари ({selected_pair}) не знайдено."

    await query.message.answer(message_text)

    # Закрийте вікно з вибором валютної пари
    await query.message.delete()


@dp.message_handler(lambda message: message.text in ["Analyse_currency"])
async def process_analyse_choice(message: types.Message):
    global user_choice
    user_choice = message.text

    if user_choice == "Analyse_currency":
        await show_currency_analys_page(message, current_page)


async def show_currency_analys_page(message, page):
    # Завантажте результати аналізу валютних пар
    currency_analys_data = load_currency_data_analys()

    # Створіть повідомлення з результатами аналізу для поточної сторінки
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_currency_pairs = list(currency_analys_data.keys())[start_index:end_index]
    currency_analys_message = f"Результати аналізу валютних пар за {previous_day}:\n"

    for currency_pair in current_currency_pairs:
        analysis_data = currency_analys_data[currency_pair]
        rmse = analysis_data.get("RMSE", "N/A")
        mae = analysis_data.get("MAE", "N/A")
        actual_change = analysis_data.get("actual_change", "N/A")
        predict_change = analysis_data.get("predict_change", "N/A")

        currency_analys_message += f"{currency_pair}\n"
        currency_analys_message += f"RMSE: {rmse}\n"
        currency_analys_message += f"MAE: {mae}\n"
        currency_analys_message += f"Actual Change: {actual_change}\n"
        currency_analys_message += f"Predicted Change: {predict_change}\n\n"

    await message.answer(currency_analys_message)

    # Побудуйте клавіатуру пагінації
    pagination_keyboard = InlineKeyboardMarkup()
    if page > 1:
        pagination_keyboard.add(
            InlineKeyboardButton(
                text="← Previous", callback_data="prev_page_analys_currency"
            )
        )
    if end_index < len(currency_analys_data):
        pagination_keyboard.add(
            InlineKeyboardButton(
                text="Next →", callback_data="next_page_analys_currency"
            )
        )

    await message.answer("Пагінація:", reply_markup=pagination_keyboard)


@dp.callback_query_handler(lambda query: query.data == "prev_page_analys_currency")
async def process_previous_page_analys_currency(query: types.CallbackQuery):
    global current_page
    if current_page > 1:
        current_page -= 1
    await query.answer()
    await show_currency_analys_page(query.message, current_page)


@dp.callback_query_handler(lambda query: query.data == "next_page_analys_currency")
async def process_next_page_analys_currency(query: types.CallbackQuery):
    global current_page
    current_page += 1
    await query.answer()
    await show_currency_analys_page(query.message, current_page)


async def send_messages(message):
    user_ids = read_json()
    for user_dict in user_ids:  # Iterate through each dictionary
        for (
            user_id
        ) in user_dict.values():  # Iterate through all values in the dictionary
            try:
                await bot.send_message(user_id, message)
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")


if __name__ == "__main__":
    from aiogram import executor

    # Check if the script is being run directly
    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        # Start the background task to send messages
        executor.start_polling(dp, skip_updates=True)
