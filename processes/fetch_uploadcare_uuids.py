import requests
import os
import json
from datetime import datetime, timedelta
import pytz

# === Configuration ===
UPLOADCARE_API_BASE = "https://api.uploadcare.com"
UPLOADCARE_PUBLIC_KEY = os.getenv("UPLOADCARE_PUBLIC_KEY")
UPLOADCARE_SECRET_KEY = os.getenv("UPLOADCARE_SECRET_KEY")
UUID_LIST_PATH = "files/uuid_list.json"

# === Determine latest Tuesday 6AM JST ===
def get_latest_map_week_jst():
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    days_since_tuesday = (now_jst.weekday() - 1) % 7
    last_tuesday = now_jst - timedelta(days=days_since_tuesday)
    return last_tuesday.replace(hour=6, minute=0, second=0, microsecond=0)

def fetch_recent_uploads():
    print("📥 Fetching files from Uploadcare...")

    headers = {
        "Authorization": f"Uploadcare.Simple {UPLOADCARE_PUBLIC_KEY}:{UPLOADCARE_SECRET_KEY}"
    }

    files = []
    next_url = f"{UPLOADCARE_API_BASE}/files/"
    while next_url:
        response = requests.get(next_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        files.extend(data["results"])
        next_url = data["next"]

    return files

def main():
    map_cutoff_jst = get_latest_map_week_jst()
    print(f"📅 Latest cutoff: {map_cutoff_jst.strftime('%Y-%m-%d %H:%M:%S JST')}")

    # Load old UUIDs
    existing_uuids = set()
    if os.path.exists(UUID_LIST_PATH):
        with open(UUID_LIST_PATH, "r", encoding="utf-8") as f:
            try:
                old_data = json.load(f)
                existing_uuids = {entry["uuid"] for entry in old_data}
            except json.JSONDecodeError:
                pass

    # Fetch new uploads
    files = fetch_recent_uploads()

    # Timezone
    jst = pytz.timezone("Asia/Tokyo")
    map_week_str = map_cutoff_jst.strftime("%Y-%m-%d")
    new_entries = []

    for f in files:
        uuid = f["uuid"]
        datetime_str = f["datetime_uploaded"]
        uploaded_at_utc = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        uploaded_at_jst = uploaded_at_utc.astimezone(jst)

        if uuid in existing_uuids:
            continue

        if uploaded_at_jst >= map_cutoff_jst:
            entry = {
                "uuid": uuid,
                "datetime_uploaded": uploaded_at_jst.isoformat(),
                "map_week": map_week_str
            }
            new_entries.append(entry)

    all_entries = sorted(new_entries + list(existing_uuids))
    print(f"✅ {len(new_entries)} new file(s) after {map_week_str}")

    # Save new list
    with open(UUID_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(new_entries + list(existing_uuids), f, indent=2, ensure_ascii=False)
    print(f"💾 UUID list updated at: {UUID_LIST_PATH}")

if __name__ == "__main__":
    main()