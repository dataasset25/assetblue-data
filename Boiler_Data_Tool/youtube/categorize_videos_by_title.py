#!/usr/bin/env python3
"""
Video Categorization Script - Title-Based
Categorizes downloaded videos based on keywords in their titles.
"""

import os
from pathlib import Path
import re

def categorize_by_title():
    """Categorize videos based on keywords in their titles."""
    output_dir = Path("subcritical_drum_boiler_videos")
    
    if not output_dir.exists():
        print("Download directory not found!")
        return
    
    # Define category keywords
    categories = {
        "Failure_Case": [
            "failure", "explosion", "explode", "trip", "emergency", "problem", "leakage", 
            "leak", "corrosion", "deposition", "troubleshooting", "repair", "maintenance",
            "bfp", "pump failure", "tube failure", "boiler failure"
        ],
        "Technical_Manual": [
            "operation", "procedure", "sop", "start up", "startup", "commissioning",
            "control", "system", "parameter", "efficiency", "performance", "numerical",
            "calculation", "design", "specification", "technical", "manual"
        ],
        "Troubleshooting_Maintenance": [
            "troubleshooting", "maintenance", "inspection", "repair", "service",
            "diagnosis", "fix", "solution", "prevention", "care", "upkeep"
        ],
        "Product_Documentation_Educational": [
            "animation", "demonstration", "how it works", "introduction", "overview",
            "educational", "documentation", "manufacturing", "company", "factory",
            "product", "explanation", "basics", "fundamentals", "principles"
        ]
    }
    
    # Get all MP4 files
    mp4_files = list(output_dir.glob("*.mp4"))
    
    print(f"Found {len(mp4_files)} MP4 files to categorize...")
    
    # Create category folders
    for category in categories.keys():
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)
    
    categorized_count = 0
    uncategorized = []
    
    for mp4_file in mp4_files:
        title = mp4_file.stem.lower()  # Get filename without extension
        
        # Find best matching category
        best_category = None
        max_matches = 0
        
        for category, keywords in categories.items():
            matches = 0
            for keyword in keywords:
                if keyword.lower() in title:
                    matches += 1
            
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        if best_category and max_matches > 0:
            # Move to category folder
            category_dir = output_dir / best_category
            new_path = category_dir / mp4_file.name
            
            if not new_path.exists():
                mp4_file.rename(new_path)
                print(f"✓ {best_category}: {mp4_file.name[:60]}...")
                categorized_count += 1
            else:
                print(f"⚠ Already exists: {mp4_file.name[:60]}...")
        else:
            uncategorized.append(mp4_file.name)
            print(f"❓ Uncategorized: {mp4_file.name[:60]}...")
    
    print(f"\n✅ Categorized {categorized_count} videos")
    print(f"❓ Uncategorized: {len(uncategorized)} videos")
    
    if uncategorized:
        print("\nUncategorized videos:")
        for video in uncategorized:
            print(f"  • {video}")
    
    # Show summary
    print("\n📊 Category Summary:")
    for category in categories.keys():
        category_dir = output_dir / category
        if category_dir.exists():
            count = len(list(category_dir.glob("*.mp4")))
            print(f"  {category.replace('_', ' / ')}: {count} videos")

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
    print("🎯 Starting video categorization by title...")
    categorize_by_title()
    create_category_report()
    print("\n✅ Categorization complete!")
