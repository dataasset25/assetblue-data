"""
Add cloudflare_storage column with public R2 URLs for downloaded records.
Processes both merged.csv and next_100_urls_with_status.csv.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Tuple

WORKDIR = Path(__file__).parent
MERGED_CSV = WORKDIR / "merged.csv"
NEXT_CSV = WORKDIR / "next_100_urls_with_status.csv"
DOWNLOAD_PROGRESS = WORKDIR / "download_progress.json"

# Public Cloudflare R2 base URL (account + bucket)
CLOUDFLARE_BASE_URL = (
    "https://4c9e60a2dc0dcf475cc907f3cd645f1d.r2.cloudflarestorage.com/boiler-asset"
)


def load_url_to_cloudflare() -> Dict[str, str]:
    """Build mapping URL -> Cloudflare object URL."""
    if not DOWNLOAD_PROGRESS.exists():
        raise FileNotFoundError(f"{DOWNLOAD_PROGRESS} not found")

    with open(DOWNLOAD_PROGRESS, "r", encoding="utf-8") as f:
        progress = json.load(f)

    base_dir = (WORKDIR / "downloaded_content").resolve()
    url_map: Dict[str, str] = {}

    for entry in progress.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "success":
            continue

        url = (entry.get("url") or "").strip()
        if not url:
            continue

        file_path = entry.get("file_path") or ""
        if not file_path:
            continue

        path_obj = Path(file_path)
        try:
            # Attempt to make relative to downloaded_content directory
            rel_path = path_obj.relative_to(base_dir)
        except ValueError:
            # Fallback: if already relative (e.g., html\foo.html)
            if "downloaded_content" in path_obj.parts:
                idx = path_obj.parts.index("downloaded_content")
                rel_path = Path(*path_obj.parts[idx + 1 :])
            else:
                rel_path = path_obj

        rel_key = rel_path.as_posix()
        cloudflare_url = f"{CLOUDFLARE_BASE_URL}/{rel_key}"
        url_map[url] = cloudflare_url

    return url_map


def find_column(fieldnames, target) -> str:
    """Find column name case-insensitively."""
    target_lower = target.lower()
    for name in fieldnames:
        if name.lower() == target_lower:
            return name
    raise ValueError(f"Column '{target}' not found in CSV header")


def process_csv(csv_path: Path, url_map: Dict[str, str]) -> Tuple[int, int, int]:
    """Add cloudflare_storage column to CSV."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        url_col = find_column(fieldnames, "url")
        status_col = find_column(fieldnames, "status")

        if "cloudflare_storage" not in [name.lower() for name in fieldnames]:
            fieldnames = fieldnames + ["cloudflare_storage"]

        rows = []
        filled = 0
        missing = 0
        downloaded_rows = 0

        for row in reader:
            status_value = (row.get(status_col) or "").strip().lower()
            url_value = (row.get(url_col) or "").strip()

            cloudflare_url = ""
            if status_value == "downloaded":
                downloaded_rows += 1
                cloudflare_url = url_map.get(url_value, "")
                if cloudflare_url:
                    filled += 1
                else:
                    missing += 1

            row["cloudflare_storage"] = cloudflare_url
            rows.append(row)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return downloaded_rows, filled, missing


def main():
    print("Building URL -> Cloudflare mapping...")
    url_map = load_url_to_cloudflare()
    print(f"  Loaded {len(url_map)} cloudflare URLs")

    for csv_file in [MERGED_CSV, NEXT_CSV]:
        if not csv_file.exists():
            print(f"Skipping {csv_file} (not found)")
            continue
        print(f"\nProcessing {csv_file.name}...")
        downloaded, filled, missing = process_csv(csv_file, url_map)
        print(f"  Downloaded rows: {downloaded}")
        print(f"  Cloudflare URLs populated: {filled}")
        print(f"  Missing mappings: {missing}")

        if missing > 0:
            print(
                "  ⚠ Some downloaded rows do not have matching Cloudflare entries. "
                "Verify download_progress.json contains them."
            )


if __name__ == "__main__":
    main()

