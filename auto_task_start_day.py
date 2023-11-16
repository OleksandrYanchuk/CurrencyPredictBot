import subprocess


def run_my_script():
    subprocess.run(["python", "currency_data/previous_day_data.py"])
    subprocess.run(["python", "currency_data/currency_predict_analys_rate.py"])
    subprocess.run(["python", "currency_data/download_currency_data.py"])
    subprocess.run(["python", "currency_data_with_sentimental.py"])
    subprocess.run(["python", "analys_data.py"])
    subprocess.run(["python", "prediction.py"])
    subprocess.run(["python", "data_cleaner.py"])


run_my_script()
