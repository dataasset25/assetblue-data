#!/usr/bin/env python3
"""
YouTube Video Downloader using Oxylabs High-Bandwidth Proxies
Downloads videos from subcritical drum boiler URLs
"""

import os
import sys
import random
import subprocess
import re
from pathlib import Path
import time

# Import configuration
try:
    from config import OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT, OXYLABS_PORT
except ImportError:
    print("Error: config.py file not found!")
    print("Please create config.py with your Oxylabs credentials.")
    sys.exit(1)

# Download Configuration
DOWNLOAD_DIR = "subcritical_drum_boiler_videos"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def extract_urls_from_file(file_path):
    """Extract YouTube URLs from the text file, removing duplicates."""
    urls = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Match YouTube URLs
                if 'youtube.com/watch?v=' in line:
                    urls.add(line)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found!")
        return []
    
    return list(urls)

def generate_proxy_url():
    """Generate proxy URL with random session ID for load balancing."""
    session_id = random.randint(1, 100000)
    username_with_session = f"{OXYLABS_USERNAME}-{session_id}"
    
    proxy_url = f"http://{username_with_session}:{OXYLABS_PASSWORD}@{OXYLABS_ENDPOINT}:{OXYLABS_PORT}"
    return proxy_url

def download_video(url, output_dir, retry_count=0):
    """Download a single video using yt-dlp with Oxylabs proxy."""
    proxy_url = generate_proxy_url()
    
    # Extract video ID from URL
    video_id = url.split("v=")[1].split("&")[0] if "v=" in url else "unknown"
    
    # yt-dlp command with proxy configuration
    cmd = [
        "python", "-m", "yt_dlp",
        "--proxy", proxy_url,
        "--output", f"{output_dir}/[{video_id}] %(title)s.%(ext)s",
        "--format", "18",  # Use format 18 (360p MP4) for maximum compatibility
        "--no-playlist",
        "--write-info-json",  # Save video metadata
        "--write-thumbnail",  # Save thumbnail
        "--embed-chapters",   # Embed chapters if available
        url
    ]
    
    try:
        print(f"Downloading: {url}")
        print(f"Using proxy session: {proxy_url.split('@')[0]}@...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✓ Successfully downloaded: {url}")
            return True
        else:
            print(f"✗ Failed to download {url}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout downloading {url}")
        return False
    except Exception as e:
        print(f"✗ Error downloading {url}: {str(e)}")
        return False

def main():
    """Main function to download all videos."""
    # Check if yt-dlp is installed
    try:
        subprocess.run(["python", "-m", "yt_dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: yt-dlp is not installed!")
        print("Please install it using: pip install yt-dlp")
        sys.exit(1)
    
    # Create download directory
    download_path = Path(DOWNLOAD_DIR)
    download_path.mkdir(exist_ok=True)
    
    # Extract URLs from file
    urls_file = "subcritical_drum_boiler/sub_critical_drum_boiler.txt"
    urls = extract_urls_from_file(urls_file)
    
    if not urls:
        print("No URLs found in the file!")
        return
    
    print(f"Found {len(urls)} unique YouTube URLs")
    print(f"Download directory: {download_path.absolute()}")
    
    # Download statistics
    successful = 0
    failed = 0
    failed_urls = []
    
    # Download each video
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing video...")
        
        success = False
        for retry in range(MAX_RETRIES):
            if download_video(url, str(download_path), retry):
                success = True
                successful += 1
                break
            else:
                if retry < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds... (attempt {retry + 2}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
        
        if not success:
            failed += 1
            failed_urls.append(url)
            print(f"✗ Failed to download after {MAX_RETRIES} attempts: {url}")
        
        # Add delay between downloads to be respectful
        if i < len(urls):
            time.sleep(2)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Download Summary:")
    print(f"Total URLs: {len(urls)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Download directory: {download_path.absolute()}")
    
    if failed_urls:
        print(f"\nFailed URLs:")
        for url in failed_urls:
            print(f"  - {url}")
        
        # Save failed URLs to file
        failed_file = download_path / "failed_downloads.txt"
        with open(failed_file, 'w') as f:
            for url in failed_urls:
                f.write(f"{url}\n")
        print(f"Failed URLs saved to: {failed_file}")

if __name__ == "__main__":
    # Check if credentials are configured
    if OXYLABS_USERNAME == "YOUR_USERNAME" or OXYLABS_PASSWORD == "YOUR_PASSWORD":
        print("Error: Please configure your Oxylabs credentials in the script!")
        print("Update OXYLABS_USERNAME, OXYLABS_PASSWORD, and OXYLABS_ENDPOINT variables.")
        sys.exit(1)
    
    main()
