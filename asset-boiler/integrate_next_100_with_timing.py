"""
Integrate results from Parallel AI for next 100 models
with time tracking and automatic completion summary updates
"""

import pandas as pd
from pathlib import Path
import json
import re
from datetime import datetime
import time

# Update this to match your batch results file
PARALLEL_RESULTS_CSV = Path("next_100_models_batch_5_results.csv")  # Update for each batch
ALL_URLS_CSV = Path("all_urls_combined.csv")
SUMMARY_CSV = Path("models_completion_summary.csv")
LOG_FILE = Path("integration_log_100_models.txt")

def log_message(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

def parse_json_urls(json_str):
    """Parse JSON string and extract URLs"""
    if pd.isna(json_str) or json_str == '':
        return {}
    
    try:
        # Try direct JSON parsing
        if isinstance(json_str, str):
            # Remove any leading/trailing whitespace
            json_str = json_str.strip()
            # Try to parse as JSON
            data = json.loads(json_str)
        else:
            data = json_str
        
        # Extract URLs from the structure
        urls_by_category = {}
        for category, url_list in data.items():
            if isinstance(url_list, list):
                urls_by_category[category] = [str(url).strip() for url in url_list if url and str(url).strip()]
            elif isinstance(url_list, str):
                # Single URL as string
                urls_by_category[category] = [url_list.strip()]
        
        return urls_by_category
    except json.JSONDecodeError:
        # Try to extract URLs using regex as fallback
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', str(json_str))
        if urls:
            # If we found URLs but couldn't parse JSON, return as Technical Manuals
            return {'Technical Manuals': urls}
        return {}
    except Exception as e:
        log_message(f"Error parsing JSON: {e}")
        return {}

def normalize_category(category):
    """Normalize category names to standard format"""
    category_lower = str(category).lower().strip()
    
    if 'technical' in category_lower or 'tech' in category_lower:
        return 'Technical Manuals'
    elif 'product' in category_lower:
        return 'Product Manuals'
    elif 'troubleshoot' in category_lower:
        return 'Troubleshooting Resources'
    elif 'failure' in category_lower or 'case' in category_lower:
        return 'Failure Cases'
    else:
        return category  # Return as-is if no match

def main():
    # Start time tracking - must be at the beginning of main()
    start_time = datetime.now()
    start_timestamp = time.time()
    
    log_message("=" * 100)
    log_message("INTEGRATING NEXT 100 MODELS WITH TIME TRACKING")
    log_message("=" * 100)
    
    # Read Parallel AI results
    if not PARALLEL_RESULTS_CSV.exists():
        log_message(f"Error: {PARALLEL_RESULTS_CSV} not found")
        log_message("Please provide the results CSV from Parallel AI")
        return
    
    log_message(f"\nReading {PARALLEL_RESULTS_CSV}...")
    results_df = pd.read_csv(PARALLEL_RESULTS_CSV)
    log_message(f"  Found {len(results_df)} entries in results CSV")
    
    # Read all_urls_combined.csv
    if not ALL_URLS_CSV.exists():
        log_message(f"Error: {ALL_URLS_CSV} not found")
        return
    
    log_message(f"\nReading {ALL_URLS_CSV}...")
    all_urls_df = pd.read_csv(ALL_URLS_CSV)
    log_message(f"  Current entries: {len(all_urls_df)}")
    
    # Get existing Model+URL combinations for duplicate checking
    all_urls_df['URL_clean'] = all_urls_df['URL'].dropna().str.strip()
    existing_model_urls = set(
        zip(
            all_urls_df['Model'].dropna().astype(str),
            all_urls_df['URL_clean']
        )
    )
    log_message(f"  Existing unique Model+URL combinations: {len(existing_model_urls)}")
    
    # Read completion summary
    if not SUMMARY_CSV.exists():
        log_message(f"Error: {SUMMARY_CSV} not found")
        return
    
    log_message(f"\nReading {SUMMARY_CSV}...")
    summary_df = pd.read_csv(SUMMARY_CSV)
    log_message(f"  Current models in summary: {len(summary_df)}")
    
    # Process results
    new_entries = []
    stats = {
        'total_processed': 0,
        'new_urls_added': 0,
        'duplicates_skipped': 0,
        'models_updated': 0,
        'models_completed': 0,
        'categories_fulfilled': {'Technical Manuals': 0, 'Product Manuals': 0, 
                                'Troubleshooting Resources': 0, 'Failure Cases': 0}
    }
    
    log_message("\n" + "=" * 100)
    log_message("PROCESSING RESULTS")
    log_message("=" * 100)
    
    # Find the documentation_urls column (might have different names)
    doc_urls_col = None
    for col in results_df.columns:
        if 'documentation' in col.lower() or 'url' in col.lower() or 'result' in col.lower():
            doc_urls_col = col
            break
    
    if doc_urls_col is None:
        log_message("⚠ Warning: Could not find documentation_urls column. Trying all columns...")
        # Try to find JSON-like columns
        for col in results_df.columns:
            sample = str(results_df[col].iloc[0]) if len(results_df) > 0 else ''
            if '{' in sample or '[' in sample:
                doc_urls_col = col
                log_message(f"  Using column: {col}")
                break
    
    if doc_urls_col is None:
        log_message("Error: Could not find documentation URLs column in results CSV")
        return
    
    # Process each row
    for idx, row in results_df.iterrows():
        model = row.get('Model', '')
        if pd.isna(model) or model == '':
            continue
        
        stats['total_processed'] += 1
        
        # Get metadata
        asset = row.get('Asset', 'Boilers')
        subtype = row.get('Subtype', '')
        manufacturer = row.get('Manufacturer', '')
        
        # Parse documentation URLs
        doc_urls_json = row.get(doc_urls_col, '')
        urls_by_category = parse_json_urls(doc_urls_json)
        
        if not urls_by_category:
            log_message(f"  ⚠ {model}: No URLs found")
            continue
        
        # Process URLs by category
        for category, urls in urls_by_category.items():
            normalized_category = normalize_category(category)
            
            for url in urls:
                if not url or url == '':
                    continue
                
                # Check for duplicates
                model_url_key = (str(model), str(url).strip())
                if model_url_key in existing_model_urls:
                    stats['duplicates_skipped'] += 1
                    continue
                
                # Create new entry
                new_entry = {
                    'Asset': asset,
                    'Subtype': subtype,
                    'Manufacturer': manufacturer,
                    'Model': model,
                    'Category': normalized_category,
                    'URL': url.strip(),
                    'Status': '',  # Will be set when downloaded
                    'Reason': '',
                    'ContentType': 'application/pdf' if url.lower().endswith('.pdf') else '',
                    'cloudflare_storage': ''
                }
                
                new_entries.append(new_entry)
                existing_model_urls.add(model_url_key)
                stats['new_urls_added'] += 1
                stats['categories_fulfilled'][normalized_category] += 1
        
        log_message(f"  ✓ {model}: Added {len([e for e in new_entries if e['Model'] == model])} new URLs")
    
    # Add new entries to all_urls_combined.csv
    if new_entries:
        log_message(f"\n" + "=" * 100)
        log_message("ADDING NEW ENTRIES TO ALL_URLS_COMBINED.CSV")
        log_message("=" * 100)
        log_message(f"  New entries to add: {len(new_entries)}")
        
        new_df = pd.DataFrame(new_entries)
        combined_df = pd.concat([all_urls_df, new_df], ignore_index=True)
        
        log_message(f"  Saving to {ALL_URLS_CSV}...")
        combined_df.to_csv(ALL_URLS_CSV, index=False)
        log_message(f"  ✓ Saved successfully")
        log_message(f"  Total entries now: {len(combined_df)}")
    else:
        log_message("\n⚠ No new entries to add")
        combined_df = all_urls_df
    
    # Update completion summary
    log_message(f"\n" + "=" * 100)
    log_message("UPDATING MODELS_COMPLETION_SUMMARY.CSV")
    log_message("=" * 100)
    
    # Get unique models from new entries (models with URLs added)
    new_models_with_urls = set([e['Model'] for e in new_entries])
    
    # Get ALL unique models from results CSV (including those with 0 URLs)
    all_results_models = set(results_df['Model'].dropna().unique())
    
    # Combine both sets to ensure all models are processed
    all_models_to_process = new_models_with_urls | all_results_models
    log_message(f"  Models with new URLs: {len(new_models_with_urls)}")
    log_message(f"  Total models to process: {len(all_models_to_process)}")
    
    for model in all_models_to_process:
        # Count URLs by category for this model from new entries
        model_urls = [e for e in new_entries if e['Model'] == model]
        category_counts = {}
        for entry in model_urls:
            cat = entry['Category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Also count existing URLs for this model
        existing_model_urls_df = combined_df[combined_df['Model'] == model]
        for cat in ['Technical Manuals', 'Product Manuals', 'Troubleshooting Resources', 'Failure Cases']:
            existing_count = len(existing_model_urls_df[existing_model_urls_df['Category'] == cat])
            category_counts[cat] = category_counts.get(cat, 0) + existing_count
        
        # Get metadata from results CSV if model not in new_entries
        if not model_urls:
            # Try to get metadata from results CSV
            model_results = results_df[results_df['Model'] == model]
            if len(model_results) > 0:
                model_info = model_results.iloc[0]
                asset = model_info.get('Asset', 'Boilers')
                subtype = model_info.get('Subtype', '')
                manufacturer = model_info.get('Manufacturer', '')
            else:
                # Fallback - try to get from batch input CSV
                asset = 'Boilers'
                subtype = ''
                manufacturer = ''
        else:
            asset = model_urls[0]['Asset']
            subtype = model_urls[0]['Subtype']
            manufacturer = model_urls[0]['Manufacturer']
        
        # Check if model exists in summary
        model_mask = summary_df['Model'] == model
        if model_mask.any():
            # Update existing row
            idx = summary_df[model_mask].index[0]
            stats['models_updated'] += 1
        else:
            # Create new row
            idx = len(summary_df)
            new_row = {
                'Asset': asset,
                'Subtype': subtype,
                'Manufacturer': manufacturer,
                'Model': model,
                'Technical Manuals': 0,
                'Product Manuals': 0,
                'Troubleshooting Resources': 0,
                'Failure Cases': 0,
                'Total Categories Founds': 0,
                'Status': 'Incomplete',
                'Missing_Categories': '',
                'Total_URLs': 0,
                'Technical_Manual_URLs': 0,
                'Product_Manual_URLs': 0,
                'Troubleshooting_Resources_URLs': 0,
                'Failure_Cases_URLs': 0
            }
            summary_df = pd.concat([summary_df, pd.DataFrame([new_row])], ignore_index=True)
            idx = len(summary_df) - 1
        
        # Update flags and counts
        has_technical = category_counts.get('Technical Manuals', 0) > 0
        has_product = category_counts.get('Product Manuals', 0) > 0
        has_troubleshooting = category_counts.get('Troubleshooting Resources', 0) > 0
        has_failure = category_counts.get('Failure Cases', 0) > 0
        
        summary_df.at[idx, 'Technical Manuals'] = 1 if has_technical else 0
        summary_df.at[idx, 'Product Manuals'] = 1 if has_product else 0
        summary_df.at[idx, 'Troubleshooting Resources'] = 1 if has_troubleshooting else 0
        summary_df.at[idx, 'Failure Cases'] = 1 if has_failure else 0
        
        summary_df.at[idx, 'Technical_Manual_URLs'] = category_counts.get('Technical Manuals', 0)
        summary_df.at[idx, 'Product_Manual_URLs'] = category_counts.get('Product Manuals', 0)
        summary_df.at[idx, 'Troubleshooting_Resources_URLs'] = category_counts.get('Troubleshooting Resources', 0)
        summary_df.at[idx, 'Failure_Cases_URLs'] = category_counts.get('Failure Cases', 0)
        
        # Recalculate totals
        total_cats = (
            summary_df.at[idx, 'Technical Manuals'] +
            summary_df.at[idx, 'Product Manuals'] +
            summary_df.at[idx, 'Troubleshooting Resources'] +
            summary_df.at[idx, 'Failure Cases']
        )
        summary_df.at[idx, 'Total Categories Founds'] = total_cats
        
        total_urls = (
            summary_df.at[idx, 'Technical_Manual_URLs'] +
            summary_df.at[idx, 'Product_Manual_URLs'] +
            summary_df.at[idx, 'Troubleshooting_Resources_URLs'] +
            summary_df.at[idx, 'Failure_Cases_URLs']
        )
        summary_df.at[idx, 'Total_URLs'] = total_urls
        
        # Update status
        if total_cats == 4:
            summary_df.at[idx, 'Status'] = 'Completed'
            summary_df.at[idx, 'Missing_Categories'] = ''
            stats['models_completed'] += 1
        else:
            summary_df.at[idx, 'Status'] = 'Incomplete'
            missing = []
            if not has_technical:
                missing.append('Technical Manuals')
            if not has_product:
                missing.append('Product Manuals')
            if not has_troubleshooting:
                missing.append('Troubleshooting Resources')
            if not has_failure:
                missing.append('Failure Cases')
            summary_df.at[idx, 'Missing_Categories'] = ', '.join(missing)
    
    # Save updated summary
    summary_df.to_csv(SUMMARY_CSV, index=False)
    log_message(f"  ✓ Updated {SUMMARY_CSV}")
    
    # Calculate time
    end_time = datetime.now()
    end_timestamp = time.time()
    total_seconds = end_timestamp - start_timestamp
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds % 1) * 1000)
    
    # Format time display - show milliseconds if less than 1 second
    if total_seconds < 1:
        time_display = f"{milliseconds}ms ({total_seconds:.3f} seconds)"
    elif total_seconds < 60:
        time_display = f"{seconds}s ({total_seconds:.2f} seconds)"
    elif total_seconds < 3600:
        time_display = f"{minutes}m {seconds}s ({total_seconds:.2f} seconds)"
    else:
        time_display = f"{hours}h {minutes}m {seconds}s ({total_seconds:.2f} seconds)"
    
    # Final summary
    log_message("\n" + "=" * 100)
    log_message("INTEGRATION COMPLETE - FINAL SUMMARY")
    log_message("=" * 100)
    log_message(f"\nTIME TRACKING:")
    log_message(f"  Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"  End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"  Total Time: {time_display}")
    
    log_message(f"\nSTATISTICS:")
    log_message(f"  Models processed: {stats['total_processed']}")
    log_message(f"  New URLs added: {stats['new_urls_added']}")
    log_message(f"  Duplicates skipped: {stats['duplicates_skipped']}")
    log_message(f"  Models updated in summary: {stats['models_updated']}")
    log_message(f"  Models completed (all 4 categories): {stats['models_completed']}")
    
    log_message(f"\nCATEGORIES FULFILLED:")
    for cat, count in stats['categories_fulfilled'].items():
        log_message(f"  {cat}: {count} URLs")
    
    log_message(f"\nFILES UPDATED:")
    log_message(f"  ✓ {ALL_URLS_CSV} - {len(combined_df)} total entries")
    log_message(f"  ✓ {SUMMARY_CSV} - {len(summary_df)} total models")
    log_message(f"  ✓ {LOG_FILE} - Integration log saved")
    
    log_message("\n" + "=" * 100)
    log_message("INTEGRATION COMPLETE!")
    log_message("=" * 100)

if __name__ == "__main__":
    main()

