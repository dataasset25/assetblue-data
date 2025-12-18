#!/usr/bin/env python3
"""
Automatic Cleanup Script
Monitors downloads and automatically removes .part files when downloads complete
"""

import os
import time
import subprocess
from pathlib import Path
import threading

def cleanup_completed_downloads():
    """Clean up .part files and non-MP4 files."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    if not output_dir.exists():
        print("Download directory not found!")
        return
    
    # Clean up non-MP4 files first
    cleanup_non_mp4_files(output_dir)
    
    # Find all .part files
    part_files = list(output_dir.glob("*.part"))
    
    if not part_files:
        print("No .part files found.")
        return
    
    print(f"Found {len(part_files)} .part files to check...")
    
    cleaned_count = 0
    for part_file in part_files:
        try:
            # Check if the file is being used by any process
            # Try to rename it temporarily to see if it's locked
            temp_name = f"{part_file.name}.temp_check"
            temp_path = part_file.parent / temp_name
            
            try:
                part_file.rename(temp_path)
                # If rename succeeded, file is not locked
                temp_path.rename(part_file)  # Rename back
                
                # Check if corresponding .mp4 file exists (download completed)
                mp4_name = part_file.name.replace('.part', '')
                mp4_path = part_file.parent / mp4_name
                
                if mp4_path.exists():
                    print(f"✓ Download completed: {mp4_name}")
                    print(f"  Removing: {part_file.name}")
                    part_file.unlink()  # Delete the .part file
                    cleaned_count += 1
                else:
                    print(f"⏳ Still downloading: {part_file.name}")
                    
            except OSError:
                # File is locked, still being used
                print(f"🔒 Active download: {part_file.name}")
                
        except Exception as e:
            print(f"Error checking {part_file.name}: {e}")
    
    if cleaned_count > 0:
        print(f"\n✅ Cleaned up {cleaned_count} completed download files")
    else:
        print("\n📥 All downloads still in progress")

def cleanup_non_mp4_files(output_dir):
    """Remove all non-MP4 files (info.json, webp, meta, ytdl, etc.)."""
    non_mp4_extensions = ['.info.json', '.webp', '.meta', '.ytdl', '.jpg', '.png']
    
    removed_count = 0
    for ext in non_mp4_extensions:
        files = list(output_dir.glob(f"*{ext}"))
        for file in files:
            try:
                file.unlink()
                removed_count += 1
            except Exception as e:
                print(f"Could not remove {file.name}: {e}")
    
    if removed_count > 0:
        print(f"🧹 Removed {removed_count} non-MP4 files")

def monitor_downloads():
    """Continuously monitor and clean up downloads."""
    print("🔄 Starting automatic cleanup monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            cleanup_completed_downloads()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\n🛑 Cleanup monitor stopped")

def cleanup_now():
    """Run cleanup once immediately."""
    print("🧹 Running immediate cleanup...")
    cleanup_completed_downloads()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor_downloads()
    else:
        cleanup_now()
