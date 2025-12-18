# collect_bing_image_urls_per_boiler_v3.py

import requests
from bs4 import BeautifulSoup
import json
import os
import csv
import time
from urllib.parse import quote

# Paths
KEYWORDS_FOLDER = "boiler_keywords"
OUTPUT_FOLDER = "boiler_image_urls"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

# Maximum pages per keyword
MAX_PAGES = 5
IMAGES_PER_PAGE = 35  # Approx. Bing shows ~35 per page

def fetch_image_urls(keyword, max_pages=MAX_PAGES):
    """Fetch image URLs from Bing search."""
    urls = set()
    for page in range(max_pages):
        offset = page * IMAGES_PER_PAGE
        query = quote(keyword)
        url = f"https://www.bing.com/images/async?q={query}&first={offset}&count={IMAGES_PER_PAGE}&adlt=off"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            # Parse image JSON from "m" attribute
            for a_tag in soup.select("a.iusc"):
                m = a_tag.get("m")
                if not m:
                    continue
                m_json = json.loads(m)
                img_url = m_json.get("murl")
                if img_url and img_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    urls.add(img_url)
            time.sleep(1.5)  # Be polite to Bing
        except Exception as e:
            print(f"Error fetching page {page+1} for '{keyword}': {e}")
    return urls

def process_boiler_file(file_path):
    """Process a single boiler .txt file."""
    boiler_name = os.path.basename(file_path).replace(".txt", "").replace("_", " ").title()
    print(f"\n🔥 Processing {boiler_name}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # Find categories
    categories = {}
    current_category = None
    for line in open(file_path, "r", encoding="utf-8"):
        line = line.strip()
        if line.startswith("#") and "Boiler" not in line:
            current_category = line.replace("#", "").strip()
            categories[current_category] = []
        elif line and not line.startswith("#") and current_category:
            categories[current_category].append(line)

    all_urls = set()
    output_rows = []

    for category, keywords in categories.items():
        print(f"\n📂 Category: {category}")
        category_urls = set()
        for keyword in keywords:
            print(f"  🔍 Fetching: {keyword}")
            urls = fetch_image_urls(keyword)
            new_urls = urls - all_urls  # ensure uniqueness across all boilers
            category_urls.update(new_urls)
            all_urls.update(new_urls)
            print(f"    ✅ Got {len(new_urls)} new URLs ({len(category_urls)} total for {category})")
        for url in category_urls:
            output_rows.append({
                "boiler_type": boiler_name,
                "category": category,
                "image_url": url
            })

    # Write CSV
    csv_file = os.path.join(OUTPUT_FOLDER, f"{boiler_name.replace(' ', '_').lower()}_urls.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["boiler_type", "category", "image_url"])
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"✅ CSV saved: {csv_file}")

def main():
    print("=== 🔥 Collecting Bing Image URLs From Keywords Folder (Multiple Pages) ===")
    for txt_file in os.listdir(KEYWORDS_FOLDER):
        if txt_file.lower().endswith(".txt"):
            file_path = os.path.join(KEYWORDS_FOLDER, txt_file)
            process_boiler_file(file_path)

if __name__ == "__main__":
    main()
