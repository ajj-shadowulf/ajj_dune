# process_images.py
import requests
import json
import csv
import re
from PIL import Image, ImageOps
from io import BytesIO
import os

# File paths
UUID_LIST_PATH = "files/uuid_list.txt"
OUTPUT_JSON_PATH = "files/output.json"
OUTPUT_CSV_PATH = "files/output.csv"

UPLOADCARE_CDN_BASE = "https://ucarecdn.com"

def extract_area_code(text):
    match = re.search(r'([A-Z]-\d)地区', text)
    if match:
        print(f"✅ Found area code: {match.group(1)}")
        return match.group(1)
    else:
        print("⚠️ No area code found in text.")
        return None

def process_image(uuid):
    print(f"🔄 Processing UUID: {uuid}")
    url = f"{UPLOADCARE_CDN_BASE}/{uuid}/"
    response = requests.get(url)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content))
    img = ImageOps.grayscale(img)

    if img.width < 1000:
        img = img.resize((img.width * 2, img.height * 2))

    text = pytesseract.image_to_string(img, lang='jpn+eng')
    area_code = extract_area_code(text)

    return {
        "uuid": uuid,
        "text": text.strip(),
        "area_code": area_code or ""
    }

def main():
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)

    with open(UUID_LIST_PATH, "r", encoding="utf-8") as f:
        uuids = [line.strip() for line in f if line.strip()]

    results = []

    for uuid in uuids:
        try:
            result = process_image(uuid)
            results.append(result)
        except Exception as e:
            print(f"❌ Error processing {uuid}: {e}")

    # Write JSON
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON written to {OUTPUT_JSON_PATH}")

    # Write CSV
    with open(OUTPUT_CSV_PATH, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["uuid", "area_code"])
        for r in results:
            writer.writerow([r["uuid"], r["area_code"]])
    print(f"✅ CSV written to {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    import pytesseract
    main()
