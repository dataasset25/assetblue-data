import csv
import requests
import time
import json
import os
from collections import defaultdict

# Set your Parallel AI API key (set as environment variable or replace with your key)
# STEP 1: Get your API key from platform.parallel.ai (bottom of dashboard, click eye icon)
PARALLEL_API_KEY = os.getenv('PARALLEL_API_KEY', 'YOUR_PARALLEL_API_KEY_HERE')

# STEP 2: Update this URL based on Parallel AI documentation
# Check the "API REFERENCE" button on the dashboard for the correct endpoint
# Common options:
# - https://api.parallel.ai/v1/chat/completions
# - https://api.parallel.ai/v1beta/chat/completions
# - https://platform.parallel.ai/api/v1/chat
PARALLEL_API_URL = 'https://api.parallel.ai/v1/chat/completions'  # ⚠️ UPDATE THIS!

# STEP 3: Update header format if needed (check API docs)
# Options: 'Bearer' (Authorization header) or 'x-api-key' header
USE_X_API_KEY = False  # Set to True if Parallel AI uses x-api-key header

# Read the CSV file (filtered for Pumps only)
print("Reading Asset Subtypes Parallel.csv...")
rows = []
subtype_to_manufacturers = {}

with open('Asset Subtypes Parallel.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('Asset Name') and row.get('Subtype'):
            # Only process Pumps
            if row['Asset Name'].strip().lower() == 'pumps':
                rows.append(row)
                subtype = row['Subtype'].strip()
                if subtype not in subtype_to_manufacturers:
                    subtype_to_manufacturers[subtype] = None

print(f"Found {len(rows)} rows with {len(subtype_to_manufacturers)} unique subtypes (Pumps only)")

# Process each unique subtype to get manufacturers
processed = 0
for subtype in subtype_to_manufacturers.keys():
    processed += 1
    print(f"\nProcessing {processed}/{len(subtype_to_manufacturers)}: {subtype}")
    
    # Find the asset name for this subtype (use first occurrence)
    asset_name = None
    for row in rows:
        if row['Subtype'].strip() == subtype:
            asset_name = row['Asset Name']
            break
    
    prompt = f"""Generate a list of 15-20 real, well-known manufacturers that produce "{subtype}" equipment in the industrial/engineering sector.

Requirements:
- Only include real, existing companies
- Companies must actually manufacture this specific type of equipment
- Include a mix of major international manufacturers and regional leaders
- Provide company names only, one per line, without numbering or bullets
- Do not include generic terms or descriptions

Asset Category: {asset_name}
Subtype: {subtype}

Manufacturers:"""

    try:
        # Parallel AI API call
        # Adjust headers based on Parallel AI's requirements
        if USE_X_API_KEY:
            headers = {
                'x-api-key': PARALLEL_API_KEY,
                'Content-Type': 'application/json'
            }
        else:
            headers = {
                'Authorization': f'Bearer {PARALLEL_API_KEY}',
                'Content-Type': 'application/json'
            }
        
        payload = {
            'model': 'parallel-ai',  # Adjust model name as needed
            'messages': [
                {'role': 'system', 'content': 'You are an expert in industrial equipment manufacturers. Provide accurate, real-world manufacturer names for specific industrial equipment subtypes.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        response = requests.post(PARALLEL_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        # Extract response text (adjust based on Parallel AI's response structure)
        if 'choices' in response_data and len(response_data['choices']) > 0:
            manufacturers_text = response_data['choices'][0]['message']['content'].strip()
        elif 'text' in response_data:
            manufacturers_text = response_data['text'].strip()
        elif 'content' in response_data:
            manufacturers_text = response_data['content'].strip()
        else:
            manufacturers_text = str(response_data).strip()
        
        manufacturers = [m.strip() for m in manufacturers_text.split('\n') if m.strip()]
        
        # Clean up any numbering or bullets
        cleaned_manufacturers = []
        for mfg in manufacturers:
            # Remove leading numbers, bullets, dashes
            cleaned = mfg.lstrip('0123456789.-)•* ').strip()
            # Remove common prefixes
            cleaned = cleaned.replace('•', '').replace('-', '').strip()
            if cleaned and len(cleaned) > 2:
                # Remove any trailing periods or commas
                cleaned = cleaned.rstrip('.,;')
                cleaned_manufacturers.append(cleaned)
        
        # Ensure we have at least 10 manufacturers
        if len(cleaned_manufacturers) < 10:
            print(f"  Warning: Only got {len(cleaned_manufacturers)} manufacturers, requesting more...")
            additional_prompt = f"""Generate additional real manufacturers for "{subtype}" equipment. Provide 10-15 more unique manufacturer names, one per line, that are different from: {', '.join(cleaned_manufacturers[:5])}."""
            try:
                additional_payload = {
                    'model': 'parallel-ai',
                    'messages': [
                        {'role': 'user', 'content': additional_prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 800
                }
                additional_response = requests.post(PARALLEL_API_URL, headers=headers, json=additional_payload)
                additional_response.raise_for_status()
                additional_data = additional_response.json()
                
                if 'choices' in additional_data and len(additional_data['choices']) > 0:
                    additional_mfg_text = additional_data['choices'][0]['message']['content'].strip()
                elif 'text' in additional_data:
                    additional_mfg_text = additional_data['text'].strip()
                elif 'content' in additional_data:
                    additional_mfg_text = additional_data['content'].strip()
                else:
                    additional_mfg_text = str(additional_data).strip()
                
                additional_mfgs = [m.strip().lstrip('0123456789.-)•* ').strip().rstrip('.,;') 
                                   for m in additional_mfg_text.split('\n') 
                                   if m.strip() and len(m.strip()) > 2]
                cleaned_manufacturers.extend(additional_mfgs)
            except Exception as e:
                print(f"  Error getting additional manufacturers: {e}")
        
        # Limit to 20 max and remove duplicates
        seen = set()
        unique_manufacturers = []
        for mfg in cleaned_manufacturers:
            if mfg.lower() not in seen:
                seen.add(mfg.lower())
                unique_manufacturers.append(mfg)
        
        # Keep 10-20 manufacturers
        final_manufacturers = unique_manufacturers[:20]
        if len(final_manufacturers) < 10:
            final_manufacturers = unique_manufacturers  # Use all we have if less than 10
        
        subtype_to_manufacturers[subtype] = '; '.join(final_manufacturers)
        print(f"  Generated {len(final_manufacturers)} manufacturers")
        
        # Rate limiting - small delay between requests
        time.sleep(1.5)
        
    except Exception as e:
        print(f"  Error processing {subtype}: {e}")
        subtype_to_manufacturers[subtype] = f'ERROR: {str(e)}'

# Add manufacturers to each row
print("\nAdding manufacturers to rows...")
for row in rows:
    subtype = row['Subtype'].strip()
    row['Manufacturer'] = subtype_to_manufacturers.get(subtype, '')

# Write output to CSV
output_file = 'Asset Subtypes Parallel.csv'
print(f"\nWriting results to {output_file}...")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['Asset Name', 'Subtype', 'Manufacturer']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\n\nCompleted! Results saved to {output_file}")
print(f"Total rows: {len(rows)}")
print(f"Unique subtypes processed: {len(subtype_to_manufacturers)}")

