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

UPLOADCARE_PUBLIC_KEY = "e09b3ef063c5d6d265e1"  # You can replace this with your actual key if needed
UPLOADCARE_CDN_BASE = "https://ucarecdn.com"

def extract_area_code(text):
    match = re.search(r'([A-Z]-\d)地区', text)
    return match.group(1) if match else None

def process_image(uuid):
    url = f"{UPLOADCARE_CDN_BASE}/{uuid}/"
    response = requests.get(url)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content))
    img = ImageOps.grayscale(img)

    # Upscale only if width is small
    if img.width < 1000:
        img = img.resize((img.width * 2, img.height * 2))

    text = pytesseract.image_to_string(img, lang='jpn+eng')
    area_code = extract_area_code(text)

    return {
        "uuid": uuid,
        "text": text.strip(),
        "area_code": area_code
    }

def main():
    with open(UUID_LIST_PATH) as f:
        uuids = [line.strip() for line in f if line.strip()]

    results = []

    for uuid in uuids:
        try:
            result = process_image(uuid)
            results.append(result)
        except Exception as e:
            print(f"Error processing {uuid}: {e}")

    # Write JSON output
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write CSV output (uuid, area_code)
    with open(OUTPUT_CSV_PATH, "w", encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["uuid", "area_code"])
        for result in results:
            writer.writerow([result["uuid"], result["area_code"] or ""])

if __name__ == "__main__":
    import pytesseract
    main()
