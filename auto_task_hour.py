import schedule
import time
import subprocess


def run_my_script():
    subprocess.run(["python", "news_scrape.py"])


schedule.every().hour.at(":52").do(run_my_script)

while True:
    schedule.run_pending()
    time.sleep(1)
