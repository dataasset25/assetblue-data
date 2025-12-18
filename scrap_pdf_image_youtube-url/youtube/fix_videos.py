#!/usr/bin/env python3
"""
Fix Video Playback Issues
Re-downloads problematic videos with format 18 for maximum compatibility
"""

import os
import json
import subprocess
import random
from pathlib import Path

# Import configuration
try:
    from config import OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT, OXYLABS_PORT
except ImportError:
    print("Error: config.py file not found!")
    exit(1)

def generate_proxy_url():
    """Generate proxy URL with random session ID for load balancing."""
    session_id = random.randint(1, 100000)
    username_with_session = f"{OXYLABS_USERNAME}-{session_id}"
    
    proxy_url = f"http://{username_with_session}:{OXYLABS_PASSWORD}@{OXYLABS_ENDPOINT}:{OXYLABS_PORT}"
    return proxy_url

def get_video_url_from_metadata(info_file):
    """Extract video URL from metadata file."""
    try:
        with open(info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('webpage_url')
    except Exception as e:
        print(f"Error reading {info_file}: {e}")
        return None

def fix_video(video_file, output_dir):
    """Re-download a video with format 18 for compatibility."""
    # Find corresponding metadata file
    base_name = video_file.replace('.mp4', '')
    info_file = f"{base_name}.info.json"
    
    if not os.path.exists(info_file):
        print(f"No metadata file found for {video_file}")
        return False
    
    # Get original URL
    url = get_video_url_from_metadata(info_file)
    if not url:
        print(f"Could not get URL for {video_file}")
        return False
    
    # Generate new filename
    new_filename = f"fixed_{os.path.basename(video_file)}"
    new_path = os.path.join(output_dir, new_filename)
    
    # Skip if already fixed
    if os.path.exists(new_path):
        print(f"Already fixed: {new_filename}")
        return True
    
    proxy_url = generate_proxy_url()
    
    # Download with format 18
    cmd = [
        "python", "-m", "yt_dlp",
        "--proxy", proxy_url,
        "--output", new_path.replace('.mp4', '.%(ext)s'),
        "--format", "18",  # Use format 18 for maximum compatibility
        "--no-playlist",
        url
    ]
    
    try:
        print(f"Fixing: {os.path.basename(video_file)}")
        print(f"URL: {url}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✓ Successfully fixed: {new_filename}")
            return True
        else:
            print(f"✗ Failed to fix {video_file}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout fixing {video_file}")
        return False
    except Exception as e:
        print(f"✗ Error fixing {video_file}: {str(e)}")
        return False

def main():
    """Main function to fix all problematic videos."""
    output_dir = "subcritical_drum_boiler_videos"
    
    # Find all MP4 files that are not already fixed
    video_files = []
    for file in os.listdir(output_dir):
        if file.endswith('.mp4') and not file.startswith('fixed_') and not file.startswith('final_video_'):
            video_files.append(os.path.join(output_dir, file))
    
    if not video_files:
        print("No videos need fixing!")
        return
    
    print(f"Found {len(video_files)} videos to fix:")
    for video in video_files:
        print(f"  - {os.path.basename(video)}")
    
    print("\nStarting video fixes...")
    
    successful = 0
    failed = 0
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Processing...")
        
        if fix_video(video_file, output_dir):
            successful += 1
        else:
            failed += 1
        
        # Add delay between downloads
        if i < len(video_files):
            import time
            time.sleep(2)
    
    print(f"\n{'='*50}")
    print(f"Fix Summary:")
    print(f"Total videos: {len(video_files)}")
    print(f"Successfully fixed: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print(f"\nFixed videos are saved with 'fixed_' prefix")
        print("You can now delete the old problematic videos and rename the fixed ones")

if __name__ == "__main__":
    main()
