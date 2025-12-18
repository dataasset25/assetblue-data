"""
Download actual data/content from URLs in merged.csv
Downloads PDFs, HTML pages, images, and other content types
"""

import asyncio
import csv
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Dict, List, Optional
import hashlib

import aiohttp
from bs4 import BeautifulSoup

# Configuration (override via environment variables)
BASE_DIR = Path(__file__).parent
DEFAULT_INPUT = BASE_DIR / "merged.csv"
DEFAULT_OUTPUT = BASE_DIR / "downloaded_content"
INPUT_CSV = Path(os.getenv("URLS_INPUT_CSV", DEFAULT_INPUT))
OUTPUT_DIR = Path(os.getenv("URLS_OUTPUT_DIR", DEFAULT_OUTPUT))
PROGRESS_FILE = Path(os.getenv("URLS_PROGRESS_FILE", BASE_DIR / "download_progress.json"))
ERROR_LOG = Path(os.getenv("URLS_ERROR_LOG", BASE_DIR / "download_errors.json"))

# Download settings
CONCURRENT_DOWNLOADS = 20  # Parallel downloads
REQUEST_TIMEOUT = 30  # Timeout per request in seconds
REQUEST_DELAY = 0.1  # Delay between requests
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
SAVE_INTERVAL = 50  # Save progress every N downloads

# Content type handling
PDF_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', '.ico'}
DOC_EXTENSIONS = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize filename for filesystem"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('.')
    
    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename or "unnamed"


def get_file_extension(url: str, content_type: str = '') -> str:
    """Determine file extension from URL or content type"""
    # Try from URL first
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if '.' in path:
        ext = os.path.splitext(path)[1].lower()
        if ext:
            return ext
    
    # Try from content type
    content_type = content_type.lower()
    if 'pdf' in content_type:
        return '.pdf'
    elif 'html' in content_type or 'text/html' in content_type:
        return '.html'
    elif 'jpeg' in content_type or 'jpg' in content_type:
        return '.jpg'
    elif 'png' in content_type:
        return '.png'
    elif 'gif' in content_type:
        return '.gif'
    elif 'json' in content_type:
        return '.json'
    elif 'xml' in content_type:
        return '.xml'
    elif 'text' in content_type:
        return '.txt'
    
    return '.bin'  # Default binary


def generate_filename(url: str, row_data: Dict, content_type: str = '') -> str:
    """Generate a meaningful filename from URL and row data"""
    # Create base name from row data
    parts = []
    if row_data.get('Manufacturer'):
        parts.append(sanitize_filename(row_data['Manufacturer'], 30))
    if row_data.get('Model'):
        parts.append(sanitize_filename(row_data['Model'], 30))
    if row_data.get('Category'):
        parts.append(sanitize_filename(row_data['Category'], 20))
    
    base_name = '_'.join(parts) if parts else 'download'
    
    # Get extension
    ext = get_file_extension(url, content_type)
    
    # Add URL hash to ensure uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    return f"{base_name}_{url_hash}{ext}"


def load_progress() -> Dict:
    """Load download progress"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_progress(progress: Dict):
    """Save download progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def load_errors() -> List[Dict]:
    """Load error log"""
    if os.path.exists(ERROR_LOG):
        try:
            with open(ERROR_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_errors(errors: List[Dict]):
    """Save error log"""
    with open(ERROR_LOG, 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=2)


async def download_url(
    session: aiohttp.ClientSession,
    url: str,
    row_data: Dict,
    output_base: Path,
    progress: Dict,
    errors: List[Dict]
) -> Dict:
    """Download content from a single URL"""
    url_id = hashlib.md5(url.encode()).hexdigest()
    
    # Skip if already downloaded
    if url_id in progress and progress[url_id].get('status') == 'success':
        return progress[url_id]
    
    result = {
        'url': url,
        'url_id': url_id,
        'row_data': row_data,
        'status': 'pending',
        'file_path': None,
        'file_size': 0,
        'content_type': None,
        'error': None
    }
    
    try:
        # Make request
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT), allow_redirects=True) as response:
            if response.status != 200:
                result['status'] = 'error'
                result['error'] = f"HTTP {response.status}"
                errors.append(result)
                return result
            
            # Get content type
            content_type = response.headers.get('Content-Type', '').lower()
            result['content_type'] = content_type
            
            # Check file size
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > MAX_FILE_SIZE:
                result['status'] = 'error'
                result['error'] = f"File too large: {content_length} bytes"
                errors.append(result)
                return result
            
            # Read content
            content = await response.read()
            
            # Check size after download
            if len(content) > MAX_FILE_SIZE:
                result['status'] = 'error'
                result['error'] = f"File too large: {len(content)} bytes"
                errors.append(result)
                return result
            
            # Determine file type and save location
            ext = get_file_extension(url, content_type)
            
            if ext in PDF_EXTENSIONS or 'pdf' in content_type:
                save_dir = output_base / 'pdfs'
            elif ext in IMAGE_EXTENSIONS or 'image' in content_type:
                save_dir = output_base / 'images'
            elif ext in DOC_EXTENSIONS or any(doc in content_type for doc in ['msword', 'spreadsheet', 'presentation']):
                save_dir = output_base / 'documents'
            elif ext == '.html' or 'html' in content_type:
                save_dir = output_base / 'html'
            else:
                save_dir = output_base / 'other'
            
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = generate_filename(url, row_data, content_type)
            file_path = save_dir / filename
            
            # Handle duplicates
            counter = 1
            original_path = file_path
            while file_path.exists():
                name, ext = os.path.splitext(original_path.name)
                file_path = save_dir / f"{name}_{counter}{ext}"
                counter += 1
            
            # Save file
            file_path.write_bytes(content)
            
            result['status'] = 'success'
            result['file_path'] = str(file_path.relative_to(output_base))
            result['file_size'] = len(content)
            
            # For HTML files, also extract text content
            if ext == '.html' or 'html' in content_type:
                try:
                    soup = BeautifulSoup(content, 'html.parser')
                    # Remove scripts and styles
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    text = soup.get_text(separator=' ', strip=True)
                    text = ' '.join(text.split())[:10000]  # Limit to 10k words
                    
                    # Save text version
                    text_path = save_dir / f"{file_path.stem}_text.txt"
                    text_path.write_text(text, encoding='utf-8')
                    result['text_path'] = str(text_path.relative_to(output_base))
                except:
                    pass  # Ignore text extraction errors
            
    except asyncio.TimeoutError:
        result['status'] = 'error'
        result['error'] = "Request timeout"
        errors.append(result)
    except aiohttp.ClientError as e:
        result['status'] = 'error'
        result['error'] = f"Client error: {str(e)[:100]}"
        errors.append(result)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Error: {str(e)[:100]}"
        errors.append(result)
    
    # Update progress
    progress[url_id] = result
    
    return result


async def download_batch(
    urls_data: List[Dict],
    output_base: Path,
    progress: Dict,
    errors: List[Dict],
    semaphore: asyncio.Semaphore
):
    """Download a batch of URLs with concurrency control"""
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for url_data in urls_data:
            async with semaphore:
                task = download_url(
                    session,
                    url_data['url'],
                    url_data['row_data'],
                    output_base,
                    progress,
                    errors
                )
                tasks.append(task)
                await asyncio.sleep(REQUEST_DELAY)  # Small delay between requests
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


def read_urls_from_csv(csv_path: str) -> List[Dict]:
    """Read URLs and associated data from CSV"""
    urls_data = []
    
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('URL', '') or row.get('url', '')
            url = url.strip()
            if url and url.startswith(('http://', 'https://')):
                urls_data.append({
                    'url': url,
                    'row_data': row
                })
    
    return urls_data


async def main():
    """Main download function"""
    print("=" * 80)
    print("URL Content Downloader")
    print("=" * 80)
    
    # Load URLs
    print(f"\nReading URLs from: {INPUT_CSV}")
    urls_data = read_urls_from_csv(INPUT_CSV)
    print(f"Found {len(urls_data)} URLs to download")
    
    # Load progress
    progress = load_progress()
    errors = load_errors()
    
    # Filter out already downloaded URLs
    downloaded_ids = {pid for pid, pdata in progress.items() if pdata.get('status') == 'success'}
    url_ids = {hashlib.md5(url_data['url'].encode()).hexdigest() for url_data in urls_data}
    
    remaining = [url_data for url_data in urls_data 
                 if hashlib.md5(url_data['url'].encode()).hexdigest() not in downloaded_ids]
    
    print(f"Already downloaded: {len(downloaded_ids)}")
    print(f"Remaining to download: {len(remaining)}")
    
    if not remaining:
        print("\n✓ All URLs have been downloaded!")
        return
    
    # Create output directory
    output_base = Path(OUTPUT_DIR)
    output_base.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    # Statistics
    stats = {
        'total': len(urls_data),
        'downloaded': len(downloaded_ids),
        'success': 0,
        'errors': 0,
        'pdfs': 0,
        'images': 0,
        'html': 0,
        'documents': 0,
        'other': 0
    }
    
    # Process in batches
    semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)
    batch_size = 100
    
    print(f"\nStarting downloads (batch size: {batch_size}, concurrent: {CONCURRENT_DOWNLOADS})...")
    print("-" * 80)
    
    start_time = time.time()
    
    for i in range(0, len(remaining), batch_size):
        batch = remaining[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(remaining) - 1) // batch_size + 1
        
        print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} URLs)")
        
        batch_start = time.time()
        results = await download_batch(batch, output_base, progress, errors, semaphore)
        batch_elapsed = time.time() - batch_start
        
        # Update stats
        for result in results:
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    stats['success'] += 1
                    file_path = result.get('file_path', '')
                    if '/pdfs/' in file_path:
                        stats['pdfs'] += 1
                    elif '/images/' in file_path:
                        stats['images'] += 1
                    elif '/html/' in file_path:
                        stats['html'] += 1
                    elif '/documents/' in file_path:
                        stats['documents'] += 1
                    else:
                        stats['other'] += 1
                else:
                    stats['errors'] += 1
        
        print(f"  Completed in {batch_elapsed:.1f}s ({len(batch)/batch_elapsed:.1f} URLs/sec)")
        print(f"  Progress: {stats['success'] + stats['errors']}/{len(remaining)} processed")
        print(f"  Success: {stats['success']}, Errors: {stats['errors']}")
        
        # Save progress periodically
        if (i + len(batch)) % SAVE_INTERVAL == 0 or batch_num == total_batches:
            save_progress(progress)
            save_errors(errors)
            print(f"  ✓ Progress saved")
    
    total_elapsed = time.time() - start_time
    
    # Final save
    save_progress(progress)
    save_errors(errors)
    
    # Final statistics
    print("\n" + "=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"Total URLs: {stats['total']}")
    print(f"Successfully downloaded: {stats['success']}")
    print(f"Errors: {stats['errors']}")
    print(f"\nDownloaded by type:")
    print(f"  PDFs: {stats['pdfs']}")
    print(f"  Images: {stats['images']}")
    print(f"  HTML pages: {stats['html']}")
    print(f"  Documents: {stats['documents']}")
    print(f"  Other: {stats['other']}")
    print(f"\nTotal time: {total_elapsed:.1f}s ({stats['success']/total_elapsed:.1f} downloads/sec)")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Progress file: {PROGRESS_FILE}")
    print(f"Error log: {ERROR_LOG}")


if __name__ == "__main__":
    asyncio.run(main())

