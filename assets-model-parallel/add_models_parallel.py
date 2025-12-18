import asyncio
import csv
import os
from collections import OrderedDict
from typing import Dict, List, Tuple

import parallel
from parallel import AsyncParallel

# ---------- Configuration ----------
INPUT_FILE = os.path.join(os.path.dirname(__file__), "Asset Subtypes Parallel.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "Asset Subtypes Parallel Models.csv")

ROW_LIMIT_ENV = int(os.getenv("ASSET_MODEL_ROW_LIMIT", "0"))
ROW_LIMIT = ROW_LIMIT_ENV if ROW_LIMIT_ENV > 0 else None

# Parallel AI settings
PARALLEL_API_KEY = "aOgJIY6ae0Mv1pWrOhxlYE74cXetogSI2M9fSXrL" 

# Model generation settings
MIN_MODELS = 3
MAX_MODELS = 6
REQUEST_DELAY = float(os.getenv("ASSET_MODEL_REQUEST_DELAY", "0.2"))  # seconds between asset requests
SAVE_INTERVAL = 50  # Save progress every N manufacturer rows


def _build_client() -> AsyncParallel:
    if not PARALLEL_API_KEY or PARALLEL_API_KEY == "your-parallel-api-key-here":
        raise RuntimeError("PARALLEL_API_KEY is not set. Please update the API key in the code.")
    return AsyncParallel(api_key=PARALLEL_API_KEY)


def _build_output_schema(manufacturer: str, subtype: str) -> Dict[str, object]:
    return {
        "type": "json",
        "json_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "models": {
                    "type": "array",
                    "description": (
                        f"Provide {MIN_MODELS}-{MAX_MODELS} real catalog model names or series "
                        f"produced by {manufacturer} for {subtype}. Each entry must be a single "
                        "model identifier with no descriptions or extra text."
                    ),
                    "items": {
                        "type": "string",
                        "description": "Single catalog or series identifier with no commentary.",
                    },
                },
            },
            "required": ["models"],
        },
    }


async def fetch_models(client: AsyncParallel, asset: str, subtype: str, manufacturer: str) -> List[str]:
    task_input = {
        "asset": asset,
        "subtype": subtype,
        "manufacturer": manufacturer,
        "requirements": [
            f"Return {MIN_MODELS}-{MAX_MODELS} real model names or series made by {manufacturer} for {subtype}.",
            "Every model must be an actual catalog/product designation.",
            "Do not include descriptions, numbering, or duplicate models.",
            "If no verified models exist, return an empty list.",
        ],
    }

    result = await client.task_run.execute(
        input=task_input,
        processor="core",
        output=_build_output_schema(manufacturer, subtype),
        timeout=180,
    )

    output = result.output
    if output.type != "json":
        return []

    content = output.content or {}
    models = content.get("models", [])
    cleaned = []
    for model in models:
        if isinstance(model, str):
            trimmed = model.strip()
            if trimmed.upper() == "NONE":
                continue
            if trimmed:
                cleaned.append(trimmed)
    seen = set()
    unique_models = []
    for model in cleaned:
        key = model.lower()
        if key not in seen:
            seen.add(key)
            unique_models.append(model)
    return unique_models[:MAX_MODELS]


def load_rows() -> Tuple[OrderedDict, int]:
    rows_by_asset: OrderedDict[str, List[Dict[str, str]]] = OrderedDict()
    total_rows = 0
    with open(INPUT_FILE, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            asset = row.get("Asset Name", "").strip()
            subtype = row.get("Subtype", "").strip()
            manufacturer = row.get("Manufacturer", "").strip()
            url = row.get("URL", "").strip()

            if not (asset and subtype and manufacturer):
                continue

            enriched = {
                "Asset Name": asset,
                "Subtype": subtype,
                "Manufacturer": manufacturer,
                "URL": url,
                "_seq": total_rows,
            }
            rows_by_asset.setdefault(asset, []).append(enriched)
            total_rows += 1

            if ROW_LIMIT and total_rows >= ROW_LIMIT:
                break
    return rows_by_asset, total_rows


def save_models(rows_with_models: List[Dict[str, str]]) -> None:
    if not rows_with_models:
        return

    ordered_rows = sorted(rows_with_models, key=lambda r: (r.get("_seq", 0), r.get("_model_idx", 0)))
    cleaned_rows = []
    for row in ordered_rows:
        cleaned = {k: v for k, v in row.items() if not k.startswith("_")}
        cleaned_rows.append(cleaned)

    fieldnames = ["Asset Name", "Subtype", "Manufacturer", "URL", "Model"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)


class ProgressTracker:
    def __init__(self) -> None:
        self.output_rows: List[Dict[str, str]] = []
        self.total_processed = 0
        self.rows_since_save = 0
        self.lock = asyncio.Lock()

    async def record_results(self, rows: List[Dict[str, str]], processed_increment: int = 1) -> None:
        async with self.lock:
            self.output_rows.extend(rows)
            self.total_processed += processed_increment
            self.rows_since_save += processed_increment
            if self.rows_since_save >= SAVE_INTERVAL:
                await self._flush_locked(reason="interval")

    async def finalize(self) -> None:
        async with self.lock:
            await self._flush_locked(reason="final", force=True)

    async def _flush_locked(self, *, reason: str, force: bool = False) -> None:
        if not force and self.rows_since_save == 0:
            return

        rows_copy = list(self.output_rows)
        total = self.total_processed
        await asyncio.to_thread(save_models, rows_copy)
        print(f"Progress saved ({total} rows processed) [{reason}]")
        self.rows_since_save = 0


def _build_result_rows(row: Dict[str, str], models: List[str]) -> List[Dict[str, str]]:
    seq = row.get("_seq", 0)
    url = row.get("URL", "")
    base_entry = {
        "Asset Name": row["Asset Name"],
        "Subtype": row["Subtype"],
        "Manufacturer": row["Manufacturer"],
        "URL": url,
    }
    results: List[Dict[str, str]] = []

    if not models:
        entry = dict(base_entry)
        entry["Model"] = ""
        entry["_seq"] = seq
        entry["_model_idx"] = 0
        results.append(entry)
        return results

    for idx, model in enumerate(models):
        entry = dict(base_entry)
        entry["Model"] = model
        entry["_seq"] = seq
        entry["_model_idx"] = idx
        results.append(entry)
    return results


async def process_asset(asset: str, rows: List[Dict[str, str]], client: AsyncParallel, tracker: ProgressTracker) -> None:
    print(f"▶ Starting asset '{asset}' ({len(rows)} rows)")
    for row in rows:
        subtype = row["Subtype"]
        manufacturer = row["Manufacturer"]
        try:
            models = await fetch_models(client, asset, subtype, manufacturer)
        except parallel.APIError as exc:
            print(f"  [{asset}] API error for {manufacturer} – {subtype}: {exc}")
            models = []
        except Exception as exc:
            print(f"  [{asset}] Unexpected error for {manufacturer} – {subtype}: {exc}")
            models = []

        if models:
            print(f"  [{asset}] {manufacturer} – {subtype}: {len(models)} model(s)")
        else:
            print(f"  [{asset}] {manufacturer} – {subtype}: no models")

        result_rows = _build_result_rows(row, models)
        await tracker.record_results(result_rows, processed_increment=1)

        if REQUEST_DELAY > 0:
            await asyncio.sleep(REQUEST_DELAY)
    print(f"✔ Finished asset '{asset}'")


async def main() -> None:
    print(f"Reading source rows from {INPUT_FILE}")
    rows_by_asset, total_rows = load_rows()

    if total_rows == 0:
        print("No rows found to process.")
        return

    asset_count = len(rows_by_asset)
    print(f"Preparing to process {total_rows} rows across {asset_count} assets (limit={ROW_LIMIT})")

    tracker = ProgressTracker()
    async with _build_client() as client:
        tasks = [
            asyncio.create_task(process_asset(asset, rows, client, tracker))
            for asset, rows in rows_by_asset.items()
        ]
        await asyncio.gather(*tasks)

    await tracker.finalize()
    print(f"Completed processing {total_rows} rows. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

