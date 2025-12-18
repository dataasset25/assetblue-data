import pandas as pd
import requests
from io import BytesIO
import PyPDF2
import pdfplumber
import re
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def extract_text_from_pdf(pdf_url):
    """
    Extract text from PDF URL using multiple methods for better coverage.
    Returns tuple: (text, error_message)
    """
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if response is actually a PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
            # Still try to parse if URL suggests it's a PDF
            pass
        
        pdf_bytes = BytesIO(response.content)
        
        pdfplumber_error = None
        # Try pdfplumber first (better for complex PDFs)
        try:
            with pdfplumber.open(pdf_bytes) as pdf:
                text = ""
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as page_error:
                        # Continue with next page if one fails
                        continue
                if text.strip():
                    return text, None
        except Exception as e:
            # Store error for fallback
            pdfplumber_error = str(e)
        
        # Fallback to PyPDF2
        pdf_bytes.seek(0)
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_bytes)
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    # Continue with next page if one fails
                    continue
            if text.strip():
                return text, None
            else:
                return "", "PDF appears to be empty or image-based (no extractable text)"
        except Exception as e:
            error_msg = f"Both parsers failed"
            if pdfplumber_error:
                error_msg += f". pdfplumber: {pdfplumber_error}"
            error_msg += f". PyPDF2: {str(e)}"
            return "", error_msg
        
        return "", "Could not extract text - PDF may be image-based or corrupted"
    except requests.exceptions.Timeout:
        return "", "Request timeout - PDF download took too long"
    except requests.exceptions.HTTPError as e:
        return "", f"HTTP Error: {e.response.status_code} - {str(e)}"
    except requests.exceptions.RequestException as e:
        return "", f"Request Error: {str(e)}"
    except Exception as e:
        return "", f"Unexpected error: {str(e)}"

def extract_text_from_html(html_url):
    """
    Extract text from HTML URL.
    Returns tuple: (text, error_message)
    """
    try:
        # Download HTML
        response = requests.get(html_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        if text.strip():
            return text, None
        else:
            return "", "HTML page appears to be empty"
            
    except requests.exceptions.Timeout:
        return "", "Request timeout - HTML download took too long"
    except requests.exceptions.HTTPError as e:
        return "", f"HTTP Error: {e.response.status_code} - {str(e)}"
    except requests.exceptions.RequestException as e:
        return "", f"Request Error: {str(e)}"
    except Exception as e:
        return "", f"Unexpected error: {str(e)}"

def extract_text_from_url(url, content_type=None):
    """
    Extract text from URL based on content type.
    Returns tuple: (text, error_message)
    """
    # Determine content type from URL if not provided
    if not content_type:
        if '.pdf' in url.lower() or url.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif '.html' in url.lower() or url.lower().endswith('.html') or url.lower().endswith('.htm'):
            content_type = 'text/html'
        elif 'text/html' in str(content_type).lower():
            content_type = 'text/html'
    
    # Route to appropriate extractor
    if content_type == 'application/pdf' or '.pdf' in url.lower():
        return extract_text_from_pdf(url)
    elif content_type == 'text/html' or '.html' in url.lower() or '.htm' in url.lower():
        return extract_text_from_html(url)
    else:
        # Try to extract as text/plain or HTML
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            content_type_header = response.headers.get('Content-Type', '').lower()
            
            if 'html' in content_type_header:
                return extract_text_from_html(url)
            elif 'text' in content_type_header:
                text = response.text
                if text.strip():
                    return text, None
                else:
                    return "", "Content appears to be empty"
            else:
                # Try HTML parsing as fallback
                return extract_text_from_html(url)
        except Exception as e:
            return "", f"Could not determine content type or extract text: {str(e)}"

def check_model_in_content(model, content):
    """
    Check if the model is mentioned in the PDF content.
    Uses flexible matching to catch variations.
    """
    if not model or not content:
        return False
    
    # Normalize model name - remove extra spaces, handle variations
    model_normalized = model.strip().upper()
    
    # Remove common punctuation and normalize
    model_clean = re.sub(r'[^\w\s]', '', model_normalized)
    content_upper = content.upper()
    
    # Create search patterns with various formats
    patterns = [
        model_normalized,  # Exact match: "SERIES 400"
        model_clean,  # Clean version: "SERIES 400"
        model_normalized.replace(" ", ""),  # No spaces: "SERIES400"
        model_normalized.replace(" ", "-"),  # Hyphenated: "SERIES-400"
        model_normalized.replace("-", " "),  # Spaces instead of hyphens
    ]
    
    # Check each pattern
    for pattern in patterns:
        if pattern and pattern in content_upper:
            return True
    
    # Check for word boundary matches (handles cases where model might be split)
    # For "SERIES 400", check if both words appear close together
    words = model_clean.split()
    if len(words) > 1:
        # Check if all words appear in content (within reasonable distance)
        all_words_found = all(word in content_upper for word in words if word)
        if all_words_found:
            # Check if they appear close together (within 50 characters)
            for i in range(len(content_upper) - 100):
                chunk = content_upper[i:i+100]
                found_words = sum(1 for word in words if word in chunk)
                if found_words >= len(words):
                    return True
    
    # For models with numbers, also check if the number appears
    # (e.g., "SERIES 400" -> check for "400" but be careful not to be too broad)
    numbers = re.findall(r'\d+', model_normalized)
    if numbers and len(model_normalized.split()) > 1:
        # Only check number if model has multiple parts (to avoid false positives)
        for num in numbers:
            # Check if number appears near model-related keywords
            model_keywords = [w for w in words if w and not w.isdigit()]
            if model_keywords:
                # Look for number within 30 chars of a keyword
                for keyword in model_keywords:
                    pattern = f"{keyword}.*{num}|{num}.*{keyword}"
                    if re.search(pattern, content_upper, re.IGNORECASE):
                        return True
    
    # Final regex check with word boundaries
    pattern_regex = r'\b' + re.escape(model_normalized.replace(" ", r'\s+')) + r'\b'
    if re.search(pattern_regex, content, re.IGNORECASE):
        return True
    
    return False

def process_single_row(args):
    """
    Process a single row - designed for parallel execution.
    Returns: (index, result_dict) where result_dict contains Model_Related and status
    """
    idx, row, model, content_type, url = args
    
    try:
        # Extract text from URL (handles PDF, HTML, and other formats)
        extracted_text, error_msg = extract_text_from_url(url, content_type)
        
        if not extracted_text:
            error_detail = error_msg if error_msg else "Could not extract text"
            return (idx, {
                'Model_Related': f'Error: {error_detail}',
                'status': 'error',
                'message': error_detail
            })
        
        # Check if model is in content
        is_related = check_model_in_content(model, extracted_text)
        
        # Also check URL/filename as secondary indicator
        if not is_related and url:
            url_upper = url.upper()
            model_upper = model.upper().replace(" ", "_").replace("-", "_")
            if model_upper in url_upper or model.replace(" ", "").upper() in url_upper:
                pass  # Still mark as "No" since user wants content-based check
        
        if is_related:
            return (idx, {
                'Model_Related': 'Yes',
                'status': 'related'
            })
        else:
            return (idx, {
                'Model_Related': 'No',
                'status': 'not_related'
            })
            
    except Exception as e:
        return (idx, {
            'Model_Related': f'Error: {str(e)}',
            'status': 'error',
            'message': str(e)
        })

def process_csv(input_file, output_file=None, max_rows=None, num_threads=5):
    """
    Process CSV file and check if PDFs match their models.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (if None, updates input_file)
        max_rows: Maximum number of rows to process (None for all)
    """
    print(f"Reading CSV file: {input_file}")
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            print(f"Successfully read CSV with {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Could not read CSV file with any of the tried encodings: {encodings}")
    
    # Initialize the new column if it doesn't exist
    if 'Model_Related' not in df.columns:
        df['Model_Related'] = ''
    
    # Process ALL rows that have a URL (Cloudflare_Storage or original URL)
    has_cloudflare = (df['Cloudflare_Storage'].notna()) & (df['Cloudflare_Storage'] != '')
    has_original_url = (df['URL'].notna()) & (df['URL'] != '')
    
    # Get all rows with URLs (any content type)
    all_rows_with_urls = df[has_cloudflare | has_original_url].copy()
    
    # Filter out rows that already have Model_Related filled (for resuming)
    # Check for rows that are already processed (have non-empty Model_Related)
    # Important: Check for valid results (Yes, No, or Error messages)
    processed_mask = (
        (all_rows_with_urls['Model_Related'].notna()) & 
        (all_rows_with_urls['Model_Related'] != '') &
        (all_rows_with_urls['Model_Related'].str.strip() != '')  # Not just whitespace
    )
    
    already_processed = all_rows_with_urls[processed_mask].copy()
    rows_to_process = all_rows_with_urls[~processed_mask].copy()
    
    # Preserve original index - don't reset, keep original CSV row numbers
    
    # Show resume statistics
    if len(already_processed) > 0:
        print(f"\n[RESUME MODE] Found {len(already_processed)} already processed rows")
        print(f"  Skipping rows that already have Model_Related filled")
        print(f"  Continuing from next unprocessed row...")
    
    # Limit rows if specified (only limit unprocessed rows)
    if max_rows:
        rows_to_process = rows_to_process.head(max_rows)
        print(f"\nLimiting to first {max_rows} unprocessed rows")
    
    total_rows = len(rows_to_process)
    total_with_urls = len(all_rows_with_urls)
    print(f"\nFound {total_rows} rows to process (out of {total_with_urls} rows with URLs)")
    if len(already_processed) > 0:
        print(f"  ({len(already_processed)} rows already processed, {total_rows} remaining)")
    
    # Show breakdown by content type
    if 'ContentType' in df.columns:
        content_types = rows_to_process['ContentType'].value_counts()
        print(f"\nContent types breakdown:")
        for ct, count in content_types.head(10).items():
            print(f"  - {ct}: {count}")
        if len(content_types) > 10:
            print(f"  - ... and {len(content_types) - 10} more types")
    
    # Calculate starting point for display
    if len(already_processed) > 0:
        # Get the first unprocessed row number
        if len(rows_to_process) > 0:
            first_unprocessed_idx = rows_to_process.index[0]
            start_row_num = first_unprocessed_idx + 1  # CSV is 1-indexed
            print(f"\nStarting from CSV row {start_row_num} (after {len(already_processed)} processed rows)")
        else:
            print(f"\nAll rows with URLs have been processed!")
            return
    else:
        if len(rows_to_process) > 0:
            first_idx = rows_to_process.index[0]
            start_row_num = first_idx + 1
            print(f"\nStarting from CSV row {start_row_num} (fresh start)")
    
    # Prepare rows for parallel processing
    print(f"\nUsing {num_threads} parallel threads for faster processing...")
    rows_data = []
    for idx, row in rows_to_process.iterrows():
        model = row['Model']
        content_type = row.get('ContentType', '')
        
        # Use Cloudflare_Storage if available, otherwise use original URL
        if pd.notna(row['Cloudflare_Storage']) and row['Cloudflare_Storage'] != '':
            url = row['Cloudflare_Storage']
        elif pd.notna(row['URL']) and row['URL'] != '':
            url = row['URL']
        else:
            df.at[idx, 'Model_Related'] = 'Error: No URL available'
            continue
        
        rows_data.append((idx, row, model, content_type, url))
    
    # Thread-safe progress tracking
    processed_lock = threading.Lock()
    processed_count = 0
    save_interval = 50  # Save after every 50 rows
    save_path = output_file if output_file else input_file
    
    # Process rows in parallel
    def update_progress(idx, result, actual_row_num):
        nonlocal processed_count
        with processed_lock:
            processed_count += 1
            df.at[idx, 'Model_Related'] = result['Model_Related']
            
            # Display progress
            status_icon = "[OK]" if result['status'] == 'related' else "[X]" if result['status'] == 'not_related' else "[WARNING]"
            status_text = "Related" if result['status'] == 'related' else "Not Related" if result['status'] == 'not_related' else result.get('message', 'Error')
            print(f"[{processed_count}/{total_rows}] CSV row {actual_row_num}: {status_icon} {status_text}")
            
            # Save progress every 50 rows
            if processed_count % save_interval == 0:
                df.to_csv(save_path, index=False, encoding='utf-8-sig')
                print(f"  [SAVED] Progress saved ({processed_count}/{total_rows} processed, last row: {actual_row_num})")
    
    # Execute parallel processing
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks
        future_to_row = {
            executor.submit(process_single_row, row_data): row_data 
            for row_data in rows_data
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_row):
            row_data = future_to_row[future]
            idx, _, _, _, _ = row_data
            actual_row_num = idx + 1
            
            try:
                idx_result, result = future.result()
                update_progress(idx_result, result, actual_row_num)
            except Exception as e:
                with processed_lock:
                    processed_count += 1
                    df.at[idx, 'Model_Related'] = f'Error: {str(e)}'
                    print(f"[{processed_count}/{total_rows}] CSV row {actual_row_num}: [ERROR] {str(e)}")
    
    # Save the updated CSV
    if output_file is None:
        output_file = input_file
    
    print(f"\nSaving final results to: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Done!")
    
    # Print summary
    related_count = len(df[df['Model_Related'] == 'Yes'])
    not_related_count = len(df[df['Model_Related'] == 'No'])
    error_count = len(df[df['Model_Related'].str.contains('Error', na=False)])
    
    print(f"\nSummary:")
    print(f"  Total processed: {processed_count}")
    print(f"  Related: {related_count}")
    print(f"  Not Related: {not_related_count}")
    print(f"  Errors: {error_count}")

if __name__ == "__main__":
    import sys
    
    input_file = "Book1.csv"
    output_file = None  # Update original file by default
    max_rows = None
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2] if sys.argv[2].lower() != 'none' else None
    if len(sys.argv) > 3:
        if sys.argv[3].lower() in ['none', '']:
            max_rows = None
        else:
            max_rows = int(sys.argv[3])
    
    num_threads = 5  # Default to 5 threads for parallel processing
    if len(sys.argv) > 4:
        num_threads = int(sys.argv[4])
    
    process_csv(input_file, output_file, max_rows, num_threads)

