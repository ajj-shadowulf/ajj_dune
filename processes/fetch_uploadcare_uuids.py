import os
import json
import requests
from datetime import datetime, timedelta, timezone
import pytz

UPLOADCARE_API_BASE = "https://api.uploadcare.com"
UPLOADCARE_CDN_BASE = "https://ucarecdn.com"
UPLOADCARE_PUBLIC_KEY = os.environ.get("UPLOADCARE_PUBLIC_KEY")
UPLOADCARE_SECRET_KEY = os.environ.get("UPLOADCARE_SECRET_KEY")

UUID_LIST_PATH = "files/uuid_list.txt"
JST = pytz.timezone("Asia/Tokyo")


def get_latest_tuesday_6am_jst(now=None):
    if not now:
        now = datetime.now(JST)
    weekday = now.weekday()  # Monday is 0, Sunday is 6
    days_since_tuesday = (weekday - 1) % 7
    latest_tuesday = now - timedelta(days=days_since_tuesday)
    latest_tuesday_6am = latest_tuesday.replace(hour=6, minute=0, second=0, microsecond=0)
    if now < latest_tuesday_6am:
        latest_tuesday_6am -= timedelta(days=7)
    return latest_tuesday_6am


def fetch_uploadcare_files():
    print("📥 Fetching files from Uploadcare...")
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
        files.extend(data.get("results", []))
        url = data.get("next")  # pagination

    return files


def load_existing_uuids():
    if not os.path.exists(UUID_LIST_PATH):
        return set()
    with open(UUID_LIST_PATH, "r", encoding="utf-8") as f:
        return set(json.loads(line.strip())["uuid"] for line in f if line.strip())


def main():
    cutoff_dt_jst = get_latest_tuesday_6am_jst()
    print(f"📅 Latest cutoff: {cutoff_dt_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    existing_uuids = load_existing_uuids()
    print(f"📂 Existing UUIDs loaded: {len(existing_uuids)}")

    all_files = fetch_uploadcare_files()
    print(f"📸 Files retrieved from Uploadcare: {len(all_files)}")

    new_entries = []

    for file in all_files:
        uuid = file["uuid"]
        if uuid in existing_uuids:
            continue

        uploaded_dt_utc = datetime.fromisoformat(file["datetime_uploaded"].replace("Z", "+00:00"))
        uploaded_dt_jst = uploaded_dt_utc.astimezone(JST)

        if uploaded_dt_jst < cutoff_dt_jst:
            continue  # Skip older files

        map_week = get_latest_tuesday_6am_jst(uploaded_dt_jst).strftime("%Y-%m-%d")

        new_entries.append({
            "uuid": uuid,
            "uploaded": uploaded_dt_jst.strftime("%Y-%m-%d %H:%M:%S"),
            "map_week": map_week
        })

    print(f"✅ New entries added: {len(new_entries)}")

    # Combine with existing entries (add dummy structure for older ones)
    existing_entries = [
        {"uuid": uuid, "uploaded": None, "map_week": None}
        for uuid in existing_uuids
    ]

    all_entries = new_entries + existing_entries
    all_entries.sort(key=lambda x: x["uploaded"] or "")

    # Write updated list
    os.makedirs(os.path.dirname(UUID_LIST_PATH), exist_ok=True)
    with open(UUID_LIST_PATH, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"📁 UUID list written to {UUID_LIST_PATH}")


if __name__ == "__main__":
    main()