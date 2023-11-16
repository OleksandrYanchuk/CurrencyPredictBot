import asyncio
import csv

import os
import subprocess

import pandas as pd
from dataclasses import dataclass, astuple, fields, field
from typing import List
from urllib.parse import urljoin


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common import (
    NoSuchElementException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from predict_bot import send_messages


BASE_URL = "https://www.investing.com"
URLS = {
    "currency_news": urljoin(BASE_URL, "/news/forex-news"),
}


@dataclass
class New:
    title: str = ""
    description: List[str] = field(default_factory=list)
    url: str = ""
    date: str = ""

    def __repr__(self):
        return f"{self.title}\n{self.url}"


NEW_FIELDS = [field.name for field in fields(New)]


def get_single_new(new_url: str, driver: WebDriver) -> New:
    driver.get(new_url)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".articleHeader"))
    )
    title = driver.find_element(By.CLASS_NAME, "articleHeader").text
    print(title)

    description_elements = driver.find_elements(
        By.CSS_SELECTOR, ".WYSIWYG.articlePage p"
    )
    description = [desc.text for desc in description_elements]

    url_element = driver.find_element(By.CSS_SELECTOR, "link[rel='canonical']")
    url = url_element.get_attribute("href") if url_element else ""
    print(url)

    # Extract publication date and update date
    try:
        date_elements = driver.find_elements(
            By.XPATH,
            "//div[@class='contentSectionDetails']//*[contains(text(), 'Published') or contains(text(), 'Updated')]",
        )

        publication_date = None
        update_date = None

        for date_element in date_elements:
            date_str = date_element.text
            if "Published" in date_str:
                publication_date = date_str.replace("Published ", "")
            elif "Updated" in date_str:
                update_date = date_str.replace("Updated ", "")

        # Choose the update date if present, otherwise use the publication date
        final_date_str = update_date or publication_date

        date_obj = datetime.strptime(final_date_str, "%b %d, %Y %I:%M%p ET")
        formatted_date = date_obj.strftime("%Y.%m.%d %I:%M")
        print(date_obj)
    except NoSuchElementException:
        # Skip the news article if neither 'Published' nor 'Updated' date is found
        print(f"Skipping news without publication or update date: {title}")
        return None

    new_data = New(title=title, description=description, url=url, date=formatted_date)

    return new_data


def get_news_from_page(page_url: str, driver: WebDriver) -> List[New]:
    driver.get(page_url)
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")

    if cookies:
        cookies[0].click()

    news_list = []

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "js-article-item"))
        )

        # Check if it's the start page
        is_start_page = "largeTitle" in driver.page_source

        if is_start_page:
            # Get all news articles on the start page
            soup = BeautifulSoup(driver.page_source, "html.parser")
            parent_div = soup.find("div", class_="largeTitle")
            news_elements = (
                parent_div.find_all("article", class_="js-article-item")
                if parent_div
                else []
            )

            # Check if no news articles are found on the page
            if not news_elements:
                print("No news found on the start page. Stopping.")
                return news_list

            for news_element in news_elements:
                # Extract relevant information from the news element
                news_url = BASE_URL + news_element.select_one("a.title").get("href")

                # Process the single news and check its publication date
                new_data = get_single_new(news_url, driver)

                if new_data:
                    # Continue processing the news article if the publication date is available
                    news_list.append(new_data)

                    # Check if the publication date is not from today
                    today = datetime.now().date()
                    publication_date = datetime.strptime(
                        new_data.date, "%Y.%m.%d %I:%M"
                    ).date()

                    if publication_date != today:
                        print("Reached an old news article. Stopping further parsing.")
                        news_list.pop()
                        break
                else:
                    # Skip this news and stop parsing if publication date is not found
                    break

    except Exception as e:
        print(f"An error occurred: {e}")

    return news_list


async def get_all_news() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    with webdriver.Chrome(options=chrome_options) as driver:
        for name, url in URLS.items():
            # Create a path for the file according to the new format
            file_path = f"currency_data/{name}_page_{datetime.today().date()}.csv"

            all_news = []  # Create a list for all news
            processed_urls = set()  # Create a set for processed URLs

            current_page = 1  # Initialize the current page here
            while True:
                page_url = url  # Create a separate variable for the page URL
                if current_page > 1:
                    page_url += f"/{current_page}"  # Update the URL for the next page

                if page_url in processed_urls:
                    print(f"Page {page_url} is already processed. Skipping.")
                    break  # Break parsing if the page is already processed
                else:
                    news = get_news_from_page(page_url, driver)

                    if not news:
                        print("No news found. Stopping.")
                        break  # Break parsing if no news is found

                    # Check if there are news in the file and add only new ones
                    if os.path.exists(file_path):
                        existing_news = pd.read_csv(file_path)
                    else:
                        existing_news = pd.DataFrame(columns=NEW_FIELDS)

                    existing_urls = set(existing_news["url"].values)

                    new_news = [n for n in news if n.url not in existing_urls]
                    for news in new_news:
                        await send_messages(f"{news.title}\n{news.url}")

                    if not new_news:
                        print("No new news found. Stopping.")
                        break  # Break parsing if no new news is found

                    print(f"Publication Date: {new_news[0].date}")

                    if not new_news[0].date.startswith(
                        datetime.now().strftime("%Y.%m.%d")
                    ):
                        print("Skipping old news.")
                        break  # Break parsing if the news is old

                    all_news.extend(new_news)
                    processed_urls.add(page_url)  # Add the processed URL
                    write_news_to_csv(file_path, all_news)  # Write news to the file
                    if new_news:
                        # You can customize the condition for running the auto_task script.
                        # For example, you can run it whenever there are new articles.
                        print("Running auto_task script...")
                        run_auto_task()

                next_page = current_page + 1
                current_page = next_page


def run_auto_task():
    subprocess.run(["python", "open_ai_predict.py"])
    subprocess.run(["python", "currency_data_with_sentimental.py"])
    subprocess.run(["python", "analys_data.py"])
    subprocess.run(["python", "prediction.py"])


def write_news_to_csv(file_path: str, news: List[New]) -> None:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(NEW_FIELDS)
        writer.writerows([astuple(new) for new in news])


if __name__ == "__main__":
    try:
        asyncio.run(get_all_news())
    except Exception as e:
        print(f"An error occurred: {e}")
