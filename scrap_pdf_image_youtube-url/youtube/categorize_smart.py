#!/usr/bin/env python3
"""
Smart Video Categorization Script
Categorizes videos by extracting video IDs from filenames or matching titles.
"""

import os
import json
from pathlib import Path
import re

def load_exact_url_categories():
    """Load exact URL-to-category mapping from the source file."""
    categories = {
        "Failure_Case": [],
        "Technical_Manual": [],
        "Troubleshooting_Maintenance": [],
        "Product_Documentation_Educational": []
    }
    
    current_category = None
    
    with open("subcritical_drum_boiler/sub_critical_drum_boiler.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Check for category headers
            if line.startswith("# Category:"):
                category_name = line.replace("# Category:", "").strip()
                # Map to folder names
                if category_name == "Failure Case":
                    current_category = "Failure_Case"
                elif category_name == "Technical / Manual":
                    current_category = "Technical_Manual"
                elif category_name == "Troubleshooting / Maintenance":
                    current_category = "Troubleshooting_Maintenance"
                elif category_name == "Product / Documentation / Educational":
                    current_category = "Product_Documentation_Educational"
                else:
                    current_category = None
                    
            elif line.startswith("https://www.youtube.com/watch?v=") and current_category:
                video_id = line.split("v=")[1].split("&")[0]
                categories[current_category].append(video_id)
    
    return categories

def extract_video_id_from_filename(filename):
    """Extract video ID from filename if it's in [ID] format."""
    # Look for pattern like [dVBoZ4PfZmE] in filename
    match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', filename)
    if match:
        return match.group(1)
    return None

def categorize_existing_videos():
    """Categorize existing videos by video ID or title matching."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    if not output_dir.exists():
        print("Download directory not found!")
        return
    
    # Load exact URL categories
    url_categories = load_exact_url_categories()
    
    # Get all MP4 files
    mp4_files = list(output_dir.glob("*.mp4"))
    
    print(f"Found {len(mp4_files)} MP4 files to categorize...")
    
    # Create category folders
    for category in url_categories.keys():
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)
    
    categorized_count = 0
    uncategorized = []
    
    for mp4_file in mp4_files:
        # Try to extract video ID from filename first
        video_id = extract_video_id_from_filename(mp4_file.name)
        
        # Find which category this video belongs to
        found_category = None
        for category, video_ids in url_categories.items():
            if video_id and video_id in video_ids:
                found_category = category
                break
        
        if found_category:
            # Move to category folder
            category_dir = output_dir / found_category
            new_path = category_dir / mp4_file.name
            
            if not new_path.exists():
                mp4_file.rename(new_path)
                print(f"✓ {found_category}: {mp4_file.name[:60]}...")
                categorized_count += 1
            else:
                print(f"⚠ Already exists: {mp4_file.name[:60]}...")
        else:
            uncategorized.append(mp4_file.name)
            print(f"❓ Uncategorized (ID: {video_id or 'N/A'}): {mp4_file.name[:50]}...")
    
    print(f"\n✅ Categorized {categorized_count} videos")
    print(f"❓ Uncategorized: {len(uncategorized)} videos")
    
    if uncategorized:
        print("\nUncategorized videos:")
        for video in uncategorized:
            print(f"  • {video}")
    
    # Show summary
    print("\n📊 Category Summary:")
    for category in url_categories.keys():
        category_dir = output_dir / category
        if category_dir.exists():
            count = len(list(category_dir.glob("*.mp4")))
            print(f"  {category.replace('_', ' / ')}: {count} videos")

def create_detailed_report():
    """Create a detailed report showing URL-to-category mapping."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    report_file = output_dir / "smart_categorization_report.txt"
    url_categories = load_exact_url_categories()
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("SMART VIDEO CATEGORIZATION REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        for category, video_ids in url_categories.items():
            f.write(f"{category.replace('_', ' / ').upper()}:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total URLs in source: {len(video_ids)}\n")
            
            # Check which videos are downloaded
            category_dir = output_dir / category
            if category_dir.exists():
                downloaded_videos = list(category_dir.glob("*.mp4"))
                f.write(f"Downloaded videos: {len(downloaded_videos)}\n\n")
                
                for video in downloaded_videos:
                    video_id = extract_video_id_from_filename(video.name)
                    f.write(f"  ✓ [{video_id}] {video.name}\n")
            else:
                f.write("Downloaded videos: 0\n\n")
            
            f.write("\n")
    
    print(f"📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    print("🎯 Starting smart video categorization...")
    categorize_existing_videos()
    create_detailed_report()
    print("\n✅ Smart categorization complete!")
