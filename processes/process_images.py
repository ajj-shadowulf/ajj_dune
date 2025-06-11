# process_images.py
import os
import requests
from PIL import Image
from PIL import ImageOps
from io import BytesIO
import pytesseract
import json

UPLOADCARE_CDN_BASE = "https://ucarecdn.com"
UUID_LIST_PATH = "files/uuid_list.txt"
OUTPUT_PATH = "files/output.json"

def get_image_text(uuid):
    url = f"{UPLOADCARE_CDN_BASE}/{uuid}/"
    response = requests.get(url)
    if response.status_code != 200:
        return {"uuid": uuid, "error": "Download failed"}

    img = Image.open(BytesIO(response.content))
    img = ImageOps.grayscale(img)   # Convert to grayscale
    img = img.resize((img.width * 2, img.height * 2))  # Upscale
    text = pytesseract.image_to_string(img, lang='jpn+eng')
    return {"uuid": uuid, "text": text.strip()}

def main():
    with open(UUID_LIST_PATH) as f:
        uuids = [line.strip() for line in f if line.strip()]

    results = []
    for uuid in uuids:
        print(f"Processing {uuid}...")
        results.append(get_image_text(uuid))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved results to output.json")

if __name__ == "__main__":
    main()
