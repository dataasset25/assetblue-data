#!/usr/bin/env python3
"""
Video Categorization Script
Categorizes downloaded videos based on their source URLs from the original text file.
"""

import os
import json
from pathlib import Path
import re

def load_url_categories():
    """Load URLs and their categories from the source file."""
    categories = {
        "Failure Case": [],
        "Technical / Manual": [],
        "Troubleshooting / Maintenance": [],
        "Product / Documentation / Educational": []
    }
    
    current_category = None
    
    with open("subcritical_drum_boiler/sub_critical_drum_boiler.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Check for category headers
            if line.startswith("# Category:"):
                category_name = line.replace("# Category:", "").strip()
                current_category = category_name
            elif line.startswith("https://www.youtube.com/watch?v="):
                if current_category and current_category in categories:
                    video_id = line.split("v=")[1].split("&")[0]
                    categories[current_category].append(video_id)
    
    return categories

def get_video_id_from_filename(filename):
    """Extract YouTube video ID from downloaded video filename."""
    # Try to find video ID in the filename (if it was saved with ID)
    # For now, we'll need to match by title since yt-dlp saves by title
    return None

def categorize_downloaded_videos():
    """Categorize all downloaded videos."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    if not output_dir.exists():
        print("Download directory not found!")
        return
    
    # Load URL categories
    url_categories = load_url_categories()
    
    # Get all MP4 files
    mp4_files = list(output_dir.glob("*.mp4"))
    
    print(f"Found {len(mp4_files)} MP4 files to categorize...")
    
    # Create category folders
    for category in url_categories.keys():
        category_dir = output_dir / category.replace(" / ", "_").replace(" ", "_")
        category_dir.mkdir(exist_ok=True)
    
    # Try to match videos by reading their info.json files
    categorized_count = 0
    
    for mp4_file in mp4_files:
        info_file = mp4_file.with_suffix('.mp4.info.json')
        
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    video_info = json.load(f)
                
                video_id = video_info.get('id', '')
                video_title = video_info.get('title', '')
                
                # Find which category this video belongs to
                found_category = None
                for category, video_ids in url_categories.items():
                    if video_id in video_ids:
                        found_category = category
                        break
                
                if found_category:
                    # Move to category folder
                    category_dir = output_dir / found_category.replace(" / ", "_").replace(" ", "_")
                    new_path = category_dir / mp4_file.name
                    
                    if not new_path.exists():
                        mp4_file.rename(new_path)
                        print(f"✓ Moved to {found_category}: {video_title[:50]}...")
                        categorized_count += 1
                    else:
                        print(f"⚠ Already exists in {found_category}: {video_title[:50]}...")
                else:
                    print(f"❓ Unknown category: {video_title[:50]}...")
                    
            except Exception as e:
                print(f"Error processing {mp4_file.name}: {e}")
        else:
            print(f"⚠ No info file for: {mp4_file.name}")
    
    print(f"\n✅ Categorized {categorized_count} videos")
    
    # Show summary
    print("\n📊 Category Summary:")
    for category in url_categories.keys():
        category_dir = output_dir / category.replace(" / ", "_").replace(" ", "_")
        if category_dir.exists():
            count = len(list(category_dir.glob("*.mp4")))
            print(f"  {category}: {count} videos")

def create_category_report():
    """Create a detailed report of categorized videos."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    report_file = output_dir / "video_categories_report.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("SUBCRITICAL DRUM BOILER VIDEOS - CATEGORY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        for category in ["Failure_Case", "Technical_Manual", "Troubleshooting_Maintenance", "Product_Documentation_Educational"]:
            category_dir = output_dir / category
            
            if category_dir.exists():
                videos = list(category_dir.glob("*.mp4"))
                f.write(f"{category.replace('_', ' / ').upper()}:\n")
                f.write("-" * 40 + "\n")
                
                for video in videos:
                    f.write(f"  • {video.name}\n")
                
                f.write(f"\nTotal: {len(videos)} videos\n\n")
    
    print(f"📄 Report saved to: {report_file}")

if __name__ == "__main__":
    print("🎯 Starting video categorization...")
    categorize_downloaded_videos()
    create_category_report()
    print("\n✅ Categorization complete!")

