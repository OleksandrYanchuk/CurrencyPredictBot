import os
from datetime import datetime, timedelta

directory = "currency_data/"
file_to_delete = datetime.today().date() - timedelta(days=2)

for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)

    if filename.endswith(f"{file_to_delete}.csv") or filename.endswith(
        f"{file_to_delete}.json"
    ):
        os.remove(file_path)
