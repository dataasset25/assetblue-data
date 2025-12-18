#!/usr/bin/env python3
"""
YouTube Video Downloader - Product / Documentation / Educational Only
Downloads only Product / Documentation / Educational videos from the subcritical drum boiler URLs using Oxylabs proxy.
"""

import subprocess
import time
import random
from pathlib import Path
from config import OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT, OXYLABS_PORT

def generate_proxy_url():
    """Generate a proxy URL with random session ID for Oxylabs."""
    session_id = random.randint(100000, 999999)
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
            print(f"✅ Successfully downloaded: {url}")
            return True
        else:
            print(f"❌ Failed to download: {url}")
            print(f"Error: {result.stderr}")
            
            # Retry logic
            if retry_count < 2:
                print(f"🔄 Retrying ({retry_count + 1}/2)...")
                time.sleep(5)
                return download_video(url, output_dir, retry_count + 1)
            else:
                print(f"❌ Max retries reached for: {url}")
                return False
                
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout downloading: {url}")
        return False
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

def load_product_documentation_educational_urls():
    """Load only Product / Documentation / Educational URLs from the source file."""
    urls = []
    in_product_section = False
    
    with open("subcritical_drum_boiler/sub_critical_drum_boiler.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Check for Product / Documentation / Educational section
            if line.startswith("# Category: Product / Documentation / Educational"):
                in_product_section = True
                continue
            elif line.startswith("# Category:"):
                in_product_section = False
                continue
            
            # Add URLs only from Product / Documentation / Educational section
            if in_product_section and line.startswith("https://www.youtube.com/watch?v="):
                urls.append(line)
    
    return urls

def main():
    """Main function to download Product / Documentation / Educational videos."""
    print("🎯 Starting Product / Documentation / Educational video downloads...")
    
    # Create output directory
    output_dir = Path("subcritical_drum_boiler_videos/Product_Documentation_Educational")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Product / Documentation / Educational URLs
    urls = load_product_documentation_educational_urls()
    print(f"📋 Found {len(urls)} Product / Documentation / Educational URLs to download")
    
    if not urls:
        print("❌ No Product / Documentation / Educational URLs found!")
        return
    
    # Download videos
    successful_downloads = 0
    failed_downloads = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n📥 Progress: {i}/{len(urls)}")
        
        if download_video(url, output_dir):
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Small delay between downloads
        time.sleep(2)
    
    print(f"\n✅ Download Summary:")
    print(f"   Successful: {successful_downloads}")
    print(f"   Failed: {failed_downloads}")
    print(f"   Total: {len(urls)}")

if __name__ == "__main__":
    main()
