# Asset Boiler Data Management

A Python-based data pipeline for managing boiler asset data, including manufacturer information, model catalogs, URL extraction, content downloading, and Cloudflare R2 storage integration.

## Overview

This repository contains scripts to process and manage boiler asset data through the following workflow:

1. **Extract Subtypes** - Extract asset subtypes from input data
2. **Extract Manufacturers** - Get manufacturer information for asset subtypes using Parallel AI
3. **Extract Models** - Generate model names for each manufacturer-subtype combination
4. **Scrape URLs** - Scrape and find product URLs, categorizing them (manuals, specifications, etc.)
5. **Download Content** - Download data from scraped URLs, populating Category, Status, Reason, and ContentType columns
6. **Upload to Cloudflare R2** - Upload downloaded content to Cloudflare R2 storage and add Cloudflare URLs
7. **Update CSV** - Maintain a comprehensive CSV with all asset information

## CSV Structure

The main output CSV (`all_urls_combined.csv`) contains the following 9 columns:

| Column | Description | Populated By |
|--------|-------------|--------------|
| `Asset` | Asset type (e.g., "Pumps") | Input data |
| `Subtype` | Asset subtype | Input data |
| `Manufacturer` | Manufacturer name | `add_manufacturers.py` |
| `Model` | Product model name | `add_models_parallel.py` |
| `Category` | URL category (manuals, specs, etc.) | `download_urls_data.py` (from scraping) |
| `URL` | Product URL | `integrate_next_100_with_timing.py` (scraping) |
| `Status` | Download status | `download_urls_data.py` |
| `Reason` | Status reason/error message | `download_urls_data.py` |
| `ContentType` | MIME type of downloaded content | `download_urls_data.py` |
| `Cloudflare_Storage` | Public R2 URL for downloaded file | `add_cloudflare_storage_links.py`, `upload_to_r2.py` |

## Scripts

### 1. `add_manufacturers.py`
Extracts manufacturer information for asset subtypes using Parallel AI API.

**Features:**
- Processes asset subtypes from input CSV
- Uses Parallel AI to identify manufacturers
- Filters for specific asset types (e.g., Pumps)

**Configuration:**
- Set `PARALLEL_API_KEY` environment variable or update in script
- Configure `PARALLEL_API_URL` based on Parallel AI documentation

### 2. `add_models_parallel.py`
Generates model names for each manufacturer-subtype combination using Parallel AI.

**Features:**
- Async processing with Parallel AI SDK
- Generates 3-6 models per manufacturer
- Progress saving and error handling

**Configuration:**
- Set `PARALLEL_API_KEY` in script or environment

### 3. `integrate_next_100_with_timing.py`
Scrapes and extracts product URLs from Parallel AI batch processing results.

**Features:**
- Processes batch results from Parallel AI web UI
- Scrapes and extracts URLs by category (manuals, specifications, etc.)
- Updates completion summary CSV
- Time tracking and logging

**Note:** This script processes results from Parallel AI web UI batch jobs. You can run batch jobs via the Parallel AI web interface and export results as CSV. This step performs URL scraping to find product URLs.

### 4. `download_urls_data.py`
Downloads actual content (PDFs, HTML, images) from scraped URLs in the CSV. This script populates the Category, Status, Reason, and ContentType columns.

**Features:**
- Downloads content from URLs found during scraping
- Async concurrent downloads (20 parallel)
- Supports PDFs, HTML, images, and documents
- Populates Category, Status, Reason, and ContentType columns
- Progress tracking and resume capability
- Error logging and retry logic

**Configuration:**
- Set `URLS_INPUT_CSV` environment variable (default: `merged.csv`)
- Set `URLS_OUTPUT_DIR` for download location (default: `downloaded_content/`)

### 5. `upload_to_r2.py`
Uploads downloaded files to Cloudflare R2 storage.

**Features:**
- S3-compatible API using boto3
- Concurrent uploads (10 workers)
- Progress tracking and resume capability
- Error handling and logging

**Configuration:**
Set environment variables:
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_R2_ACCESS_KEY_ID`
- `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
- `CLOUDFLARE_R2_BUCKET_NAME`

### 6. `add_cloudflare_storage_links.py`
Adds Cloudflare R2 public URLs to the CSV for successfully downloaded files.

**Features:**
- Maps downloaded files to R2 URLs
- Updates both `merged.csv` and `next_100_urls_with_status.csv`
- Creates `cloudflare_storage` column

## Setup

### Prerequisites

- Python 3.8+
- Parallel AI API key
- Cloudflare R2 credentials (Account ID, Access Key, Secret Key, Bucket Name)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dataasset25/asset-boiler.git
cd asset-boiler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Parallel AI
export PARALLEL_API_KEY="your-parallel-api-key"

# Cloudflare R2
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_R2_ACCESS_KEY_ID="your-access-key"
export CLOUDFLARE_R2_SECRET_ACCESS_KEY="your-secret-key"
export CLOUDFLARE_R2_BUCKET_NAME="your-bucket-name"
```

Or create a `.env` file (not tracked in git):
```
PARALLEL_API_KEY=your-parallel-api-key
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_R2_ACCESS_KEY_ID=your-access-key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret-key
CLOUDFLARE_R2_BUCKET_NAME=your-bucket-name
```

## Usage

### Workflow

1. **Extract Subtypes:**
   - Start with input data containing Asset and Subtype columns
   - Extract and prepare subtypes for processing

2. **Extract Manufacturers:**
   ```bash
   python add_manufacturers.py
   ```
   Extracts manufacturer information for each subtype using Parallel AI.

3. **Extract Models:**
   ```bash
   python add_models_parallel.py
   ```
   Generates model names for each manufacturer-subtype combination.
   Or use Parallel AI web UI for batch processing and export results as CSV.

4. **Scrape URLs:**
   ```bash
   # Update PARALLEL_RESULTS_CSV in script to match your batch results file
   python integrate_next_100_with_timing.py
   ```
   Scrapes and extracts product URLs, categorizing them (manuals, specifications, etc.).

5. **Download Data from Scraped URLs:**
   ```bash
   python download_urls_data.py
   ```
   Downloads content from the scraped URLs. This step populates the **Category**, **Status**, **Reason**, and **ContentType** columns in the CSV.

6. **Upload to Cloudflare R2:**
   ```bash
   python upload_to_r2.py
   ```
   Uploads downloaded files to Cloudflare R2 storage.

7. **Add Cloudflare URLs:**
   ```bash
   python add_cloudflare_storage_links.py
   ```
   Adds Cloudflare R2 public URLs to the CSV for successfully uploaded files.

### Using Parallel AI Web UI

Some operations can be performed via the Parallel AI web interface:

1. **Batch Processing:** Use the Parallel AI web UI to process large batches of manufacturers/models
2. **Export Results:** Export batch results as CSV files
3. **Integration:** Use `integrate_next_100.py` to integrate exported results into the main CSV

## File Structure

```
parallel/
├── add_manufacturers.py              # Extract manufacturers
├── add_models_parallel.py            # Extract models
├── integrate_next_100_with_timing.py  # Scrape and extract URLs
├── download_urls_data.py             # Download content from URLs
├── upload_to_r2.py                   # Upload to Cloudflare R2
├── add_cloudflare_storage_links.py   # Add R2 URLs to CSV
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## Notes

- Progress files allow scripts to resume from interruptions
- Some operations can be performed via Parallel AI web UI for easier batch processing
- Ensure Parallel AI API key and Cloudflare R2 credentials are properly configured


