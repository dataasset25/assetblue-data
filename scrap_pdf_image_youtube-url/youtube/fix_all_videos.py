#!/usr/bin/env python3
"""
Fix All Problematic Videos
Re-downloads all non-fixed videos with format 18 for maximum compatibility
"""

import os
import subprocess
import random
import time
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

def get_video_id_from_filename(filename):
    """Extract video ID from filename by checking if it exists in our URL list."""
    # Read the original URL file to find matching video
    try:
        with open("subcritical_drum_boiler/sub_critical_drum_boiler.txt", 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for YouTube URLs in the content
        import re
        urls = re.findall(r'https://www\.youtube\.com/watch\?v=([^&\s]+)', content)
        
        # For now, we'll use a simple approach - try to find the video by searching
        # This is a simplified approach - in a real scenario you'd want to match by title
        return urls[0] if urls else None
    except:
        return None

def fix_video_by_search(video_file, output_dir):
    """Fix a video by searching for it on YouTube."""
    # Extract a search term from the filename
    filename = os.path.basename(video_file)
    # Remove .mp4 extension and clean up
    search_term = filename.replace('.mp4', '').replace('_', ' ').replace('-', ' ')
    
    # Generate new filename
    new_filename = f"fixed_{filename}"
    new_path = os.path.join(output_dir, new_filename)
    
    # Skip if already fixed
    if os.path.exists(new_path):
        print(f"Already fixed: {new_filename}")
        return True
    
    proxy_url = generate_proxy_url()
    
    # Use yt-dlp search functionality
    cmd = [
        "python", "-m", "yt_dlp",
        "--proxy", proxy_url,
        "--output", new_path.replace('.mp4', '.%(ext)s'),
        "--format", "18",  # Use format 18 for maximum compatibility
        "--no-playlist",
        f"ytsearch1:{search_term}"  # Search for the video
    ]
    
    try:
        print(f"Fixing: {filename}")
        print(f"Search term: {search_term}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✓ Successfully fixed: {new_filename}")
            return True
        else:
            print(f"✗ Failed to fix {filename}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout fixing {filename}")
        return False
    except Exception as e:
        print(f"✗ Error fixing {filename}: {str(e)}")
        return False

def main():
    """Main function to fix all problematic videos."""
    output_dir = "subcritical_drum_boiler_videos"
    
    # List of problematic videos (non-fixed ones)
    problematic_videos = [
        "Steam Boiler Water Related Troubles⧸Problems During Operation, Scale Corrosion Carryover.mp4",
        "Dry And Wet Mode in Supercritical Boiler.mp4",
        "WORKING OF BOILER ATTEMPERATOR OR DESPUPERHEATER SYSTEM IN HINDI - POWER PLANT GYANI.mp4",
        "BOILER FURNACE EXIT GAS TEMP. (FEGT) MONITORING - EN.mp4",
        "HRSG Modules leakage test Failed , leakage from crack in the T fitting (Manufacturer defect ).mp4",
        "Beirut explosion - Multi-angle footage ｜ DW News.mp4",
        "LP turbine rotor #viral #viral #trending #youtubeshorts #ssc #ytshorts #india #ntpc #powerplant.mp4",
        "Animazione 3D Degassificatore Termochimica.mp4"
    ]
    
    # Check which files actually exist
    existing_videos = []
    for video in problematic_videos:
        video_path = os.path.join(output_dir, video)
        if os.path.exists(video_path):
            existing_videos.append(video_path)
    
    if not existing_videos:
        print("No problematic videos found to fix!")
        return
    
    print(f"Found {len(existing_videos)} problematic videos to fix:")
    for video in existing_videos:
        print(f"  - {os.path.basename(video)}")
    
    print("\nStarting video fixes...")
    
    successful = 0
    failed = 0
    
    for i, video_file in enumerate(existing_videos, 1):
        print(f"\n[{i}/{len(existing_videos)}] Processing...")
        
        if fix_video_by_search(video_file, output_dir):
            successful += 1
        else:
            failed += 1
        
        # Add delay between downloads
        if i < len(existing_videos):
            time.sleep(3)
    
    print(f"\n{'='*50}")
    print(f"Fix Summary:")
    print(f"Total videos: {len(existing_videos)}")
    print(f"Successfully fixed: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print(f"\nFixed videos are saved with 'fixed_' prefix")
        print("You can now delete the old problematic videos")

if __name__ == "__main__":
    main()
