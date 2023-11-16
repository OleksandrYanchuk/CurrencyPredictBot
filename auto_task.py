import schedule
import time
import subprocess


def run_my_script():
    subprocess.run(["python", "currency_data/download_currency_data.py"])
    subprocess.run(["python", "currency_data_with_sentimental.py"])
    subprocess.run(["python", "analys_data.py"])
    subprocess.run(["python", "prediction.py"])
    subprocess.run(["python", "data_cleaner.py"])


schedule.every().day.at("09:42").do(run_my_script)

while True:
    schedule.run_pending()
    time.sleep(1)
