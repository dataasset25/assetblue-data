"""
Upload all downloaded files to Cloudflare R2 storage
Uses S3-compatible API (boto3)
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    print("ERROR: boto3 is not installed!")
    print("Please install it with: pip install boto3")
    exit(1)

# Configuration
BASE_DIR = Path(__file__).parent
DOWNLOADED_DIR = Path(os.getenv("DOWNLOADED_DIR", BASE_DIR / "downloaded_content"))
PROGRESS_FILE = Path(os.getenv("R2_PROGRESS_FILE", BASE_DIR / "r2_upload_progress.json"))
ERROR_LOG = Path(os.getenv("R2_ERROR_LOG", BASE_DIR / "r2_upload_errors.json"))
FORCE_REUPLOAD = os.getenv("FORCE_REUPLOAD", "false").lower() in ("1", "true", "yes")

# Cloudflare R2 Configuration
# Get these from environment variables or set directly below
# Option 1: Set environment variables (recommended)
# Option 2: Set directly in this script (see below)

# Direct credentials (if not using environment variables)
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', '4c9e60a2dc0dcf475cc907f3cd645f1d')
CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID', '5e5303a97107c94772eeee1177d4649d')
CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY', 'e4b8f54458db69d6d2cb40077eb6a8c9ea79c498dbad8cbbcc920bed8683f870')
CLOUDFLARE_R2_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME', 'boiler-asset')

# Upload settings
MAX_WORKERS = 10  # Concurrent uploads
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for large files
SAVE_INTERVAL = 50  # Save progress every N uploads


def get_r2_client():
    """Create and return R2 S3 client"""
    if not all([CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY]):
        raise ValueError(
            "Missing R2 credentials! Please set:\n"
            "  - CLOUDFLARE_ACCOUNT_ID\n"
            "  - CLOUDFLARE_R2_ACCESS_KEY_ID\n"
            "  - CLOUDFLARE_R2_SECRET_ACCESS_KEY\n"
            "\nYou can set them as environment variables or edit this script."
        )
    
    # R2 endpoint URL
    endpoint_url = f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    # Create S3 client with R2 endpoint
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=CLOUDFLARE_R2_ACCESS_KEY_ID,
        aws_secret_access_key=CLOUDFLARE_R2_SECRET_ACCESS_KEY,
        region_name='auto'  # R2 uses 'auto' region
    )
    
    return s3_client


def get_content_type(file_path: Path) -> str:
    """Determine content type from file extension"""
    ext = file_path.suffix.lower()
    content_types = {
        '.pdf': 'application/pdf',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.txt': 'text/plain',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.bin': 'application/octet-stream',
        '.aspx': 'text/html',
        '.php': 'text/html',
    }
    return content_types.get(ext, 'application/octet-stream')


def upload_file(s3_client, file_path: Path, s3_key: str) -> Dict:
    """Upload a single file to R2"""
    result = {
        'file_path': str(file_path),
        's3_key': s3_key,
        'status': 'pending',
        'size': file_path.stat().st_size,
        'error': None
    }
    
    try:
        content_type = get_content_type(file_path)
        
        # Upload file
        with open(file_path, 'rb') as f:
            safe_name = file_path.name.encode('utf-8', 'ignore').decode('utf-8')
            s3_client.upload_fileobj(
                f,
                CLOUDFLARE_R2_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ContentDisposition': f'attachment; filename="{safe_name}"'
                }
            )
        
        result['status'] = 'success'
        return result
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        result['status'] = 'error'
        result['error'] = f"AWS Error {error_code}: {error_msg}"
        return result
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Error: {str(e)[:200]}"
        return result


def get_all_files() -> List[Path]:
    """Get all files from downloaded_content directory"""
    files = []
    for subdir in ['pdfs', 'html', 'images', 'documents', 'other']:
        dir_path = DOWNLOADED_DIR / subdir
        if dir_path.exists():
            files.extend(dir_path.glob('*'))
    # Filter out directories
    files = [f for f in files if f.is_file()]
    return sorted(files)


def generate_s3_key(file_path: Path) -> str:
    """Generate S3 key (path) for file"""
    # Get relative path from downloaded_content
    relative_path = file_path.relative_to(DOWNLOADED_DIR)
    # Use forward slashes for S3
    s3_key = str(relative_path).replace('\\', '/')
    return s3_key


def load_progress() -> Dict:
    """Load upload progress"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_progress(progress: Dict):
    """Save upload progress"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def load_errors() -> List[Dict]:
    """Load error log"""
    if ERROR_LOG.exists():
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


def main():
    """Main upload function"""
    print("=" * 80)
    print("Cloudflare R2 Upload Script")
    print("=" * 80)
    
    # Check credentials
    if not all([CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY]):
        print("\n❌ ERROR: Missing R2 credentials!")
        print("\nPlease set the following environment variables:")
        print("  - CLOUDFLARE_ACCOUNT_ID")
        print("  - CLOUDFLARE_R2_ACCESS_KEY_ID")
        print("  - CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        print("\nOr edit this script to add them directly.")
        print("\nSee CLOUDFLARE_R2_SETUP.md for detailed instructions.")
        return
    
    # Get R2 client
    try:
        print(f"\nConnecting to R2...")
        print(f"  Account ID: {CLOUDFLARE_ACCOUNT_ID[:10]}...")
        print(f"  Bucket: {CLOUDFLARE_R2_BUCKET_NAME}")
        s3_client = get_r2_client()
        
        # Test connection by checking if bucket exists
        try:
            s3_client.head_bucket(Bucket=CLOUDFLARE_R2_BUCKET_NAME)
            print("  ✓ Bucket found and accessible")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404':
                print(f"\n❌ ERROR: Bucket '{CLOUDFLARE_R2_BUCKET_NAME}' not found!")
                print("Please create the bucket in Cloudflare R2 dashboard first.")
            else:
                print(f"\n❌ ERROR: Cannot access bucket: {e}")
            return
    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to R2: {e}")
        return
    
    # Get all files
    print(f"\nScanning downloaded files...")
    all_files = get_all_files()
    print(f"Found {len(all_files)} files to upload")
    
    # Load progress
    progress = load_progress()
    errors = load_errors()
    
    # Filter out already uploaded files (unless forcing re-upload)
    uploaded_keys = {p.get('s3_key') for p in progress.values() if p.get('status') == 'success'}
    if FORCE_REUPLOAD:
        remaining_files = all_files
        print("FORCE_REUPLOAD enabled: all files will be uploaded again.")
    else:
        remaining_files = []
        for file_path in all_files:
            s3_key = generate_s3_key(file_path)
            if s3_key not in uploaded_keys:
                remaining_files.append(file_path)
    print(f"Already uploaded: {len(uploaded_keys)}")
    print(f"Remaining to upload: {len(remaining_files)}")
    
    if not remaining_files:
        print("\n✓ All files have been uploaded!")
        return
    
    # Statistics
    stats = {
        'total': len(all_files),
        'uploaded': len(uploaded_keys),
        'success': 0,
        'errors': 0,
        'total_size': 0
    }
    
    print(f"\nStarting upload (concurrent: {MAX_WORKERS})...")
    print("-" * 80)
    
    start_time = time.time()
    
    # Upload files with thread pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all upload tasks
        future_to_file = {}
        for file_path in remaining_files:
            s3_key = generate_s3_key(file_path)
            future = executor.submit(upload_file, s3_client, file_path, s3_key)
            future_to_file[future] = (file_path, s3_key)
        
        # Process completed uploads
        completed = 0
        for future in as_completed(future_to_file):
            file_path, s3_key = future_to_file[future]
            completed += 1
            
            try:
                result = future.result()
                progress[s3_key] = result
                
                if result['status'] == 'success':
                    stats['success'] += 1
                    stats['total_size'] += result['size']
                    print(f"  ✓ [{completed}/{len(remaining_files)}] {s3_key[:60]}...")
                else:
                    stats['errors'] += 1
                    errors.append(result)
                    print(f"  ✗ [{completed}/{len(remaining_files)}] {s3_key[:60]}... - {result['error']}")
                
                # Save progress periodically
                if completed % SAVE_INTERVAL == 0 or completed == len(remaining_files):
                    save_progress(progress)
                    save_errors(errors)
                    print(f"  💾 Progress saved ({completed}/{len(remaining_files)})")
            
            except Exception as e:
                stats['errors'] += 1
                error_result = {
                    'file_path': str(file_path),
                    's3_key': s3_key,
                    'status': 'error',
                    'error': f"Exception: {str(e)[:200]}"
                }
                progress[s3_key] = error_result
                errors.append(error_result)
                print(f"  ✗ [{completed}/{len(remaining_files)}] {s3_key[:60]}... - Exception: {e}")
    
    total_elapsed = time.time() - start_time
    
    # Final save
    save_progress(progress)
    save_errors(errors)
    
    # Final statistics
    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"Total files: {stats['total']}")
    print(f"Successfully uploaded: {stats['success']}")
    print(f"Errors: {stats['errors']}")
    print(f"Total size uploaded: {stats['total_size'] / (1024*1024):.2f} MB")
    print(f"Total time: {total_elapsed:.1f}s ({stats['success']/total_elapsed:.1f} files/sec)")
    print(f"\nBucket: {CLOUDFLARE_R2_BUCKET_NAME}")
    print(f"Progress file: {PROGRESS_FILE}")
    print(f"Error log: {ERROR_LOG}")


if __name__ == "__main__":
    main()

