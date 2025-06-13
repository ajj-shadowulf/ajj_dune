import os
import requests
import csv
from datetime import datetime

UPLOADCARE_API_BASE = "https://api.uploadcare.com"
UPLOADCARE_PUBLIC_KEY = os.getenv("UPLOADCARE_PUBLIC_KEY")
UPLOADCARE_SECRET_KEY = os.getenv("UPLOADCARE_SECRET_KEY")

UUID_LIST_PATH = "files/uuid_list.txt"
UUID_METADATA_PATH = "files/uuid_metadata.csv"

def get_existing_uuids():
    if not os.path.exists(UUID_LIST_PATH):
        return set()
    with open(UUID_LIST_PATH, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def get_all_uploadcare_files():
    files = []
    url = f"{UPLOADCARE_API_BASE}/files/"
    headers = {
        "Authorization": f"Uploadcare.Simple {UPLOADCARE_PUBLIC_KEY}:{UPLOADCARE_SECRET_KEY}",
        "Accept": "application/vnd.uploadcare-v0.5+json"
    }
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        files.extend(data["results"])
        url = data.get("next")
    return files

def update_uuid_list_and_metadata():
    print("🔄 Fetching Uploadcare file metadata...")
    existing_uuids = get_existing_uuids()
    all_files = get_all_uploadcare_files()

    new_files = [
        {"uuid": f["uuid"], "datetime_uploaded": f["datetime_uploaded"]}
        for f in all_files if f["uuid"] not in existing_uuids
    ]

    # Append to UUID list
    if new_files:
        with open(UUID_LIST_PATH, "a", encoding="utf-8") as f:
            for item in new_files:
                f.write(item["uuid"] + "\n")
        print(f"✅ Added {len(new_files)} new UUIDs to list.")

        # Write metadata to CSV
        file_exists = os.path.exists(UUID_METADATA_PATH)
        with open(UUID_METADATA_PATH, "a", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["uuid", "datetime_uploaded"])
            for item in new_files:
                writer.writerow([item["uuid"], item["datetime_uploaded"]])
        print(f"✅ Appended metadata to {UUID_METADATA_PATH}")
    else:
        print("✅ No new files found.")

if __name__ == "__main__":
    update_uuid_list_and_metadata()