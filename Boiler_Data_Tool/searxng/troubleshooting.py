"""
Targeted Troubleshooting PDF Downloader
ONLY for BFB and Waste Heat Recovery Boiler - Troubleshooting Category
"""

import os
import json
import csv
import requests
import pandas as pd
from datetime import datetime
from exa_py import Exa
from typing import List, Dict
import time
import re
from pathlib import Path
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TroubleshootingOnlyDownloader:
    def __init__(self, exa_api_key: str, base_dir: str = "downloaded_data"):
        """Initialize downloader for troubleshooting PDFs only"""
        self.exa = Exa(exa_api_key)
        self.base_dir = Path(base_dir)
        self.progress_file = self.base_dir / "troubleshooting_補完.json"
        
        self.results = []
        self.pdf_catalog = []
        self.search_count = 0
        self.download_count = 0
        self.failed_downloads = []
        self.progress_data = {
            'start_time': datetime.now().isoformat(),
            'target': 'Troubleshooting only - BFB & Waste Heat Recovery',
            'total_searches': 0,
            'total_downloads': 0
        }
        
        self.save_progress()
    
    def get_folder_name(self, boiler_type: str) -> str:
        """Convert boiler type to folder name"""
        folder_map = {
            'BFB (Bubbling Fluidized Bed)': 'bfb_bubbling_fluidized_bed',
            'Waste Heat Recovery Boiler': 'waste_heat_recovery_boiler'
        }
        return folder_map.get(boiler_type)
    
    def save_progress(self):
        """Save real-time progress"""
        self.progress_data['last_update'] = datetime.now().isoformat()
        self.progress_data['total_searches'] = self.search_count
        self.progress_data['total_downloads'] = self.download_count
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
    
    def search_pdf_documents(self, query: str, boiler_type: str, num_results: int = 20) -> List[Dict]:
        """Search for troubleshooting PDFs"""
        try:
            print(f"  🔍 Searching: {query[:75]}...")
            
            pdf_query = f"{query} filetype:pdf"
            
            result = self.exa.search_and_contents(
                pdf_query,
                type="neural",
                num_results=num_results,
                use_autoprompt=True,
                text=False,
                category="pdf"
            )
            
            self.search_count += 1
            self.save_progress()
            
            pdf_docs = []
            for item in result.results:
                if self.is_pdf_url(item.url):
                    doc = {
                        'boiler_type': boiler_type,
                        'category': 'Troubleshooting',
                        'query': query,
                        'title': item.title,
                        'url': item.url,
                        'score': getattr(item, 'score', 'N/A'),
                        'timestamp': datetime.now().isoformat(),
                        'downloaded': False,
                        'local_path': None
                    }
                    pdf_docs.append(doc)
                    self.results.append(doc)
            
            print(f"    ✅ Found {len(pdf_docs)} PDFs")
            time.sleep(0.5)
            return pdf_docs
            
        except Exception as e:
            print(f"  ❌ Search Error: {str(e)[:70]}")
            return []
    
    def is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF"""
        pdf_indicators = ['.pdf', 'pdf', 'download', 'document']
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in pdf_indicators)
    
    def sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """Create safe filename"""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace(' ', '_')
        if len(filename) > max_length:
            filename = filename[:max_length]
        return filename
    
    def download_pdf(self, doc: Dict, troubleshooting_folder: Path) -> bool:
        """Download PDF with retry logic"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                url = doc['url']
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/x-pdf,*/*'
                }
                
                response = requests.get(url, headers=headers, timeout=15, stream=True, verify=False)
                response.raise_for_status()
                break
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    self.failed_downloads.append({
                        'url': doc['url'],
                        'title': doc['title'],
                        'reason': 'Connection error'
                    })
                    return False
            except requests.exceptions.RequestException:
                self.failed_downloads.append({
                    'url': doc['url'],
                    'title': doc['title'],
                    'reason': 'Download error'
                })
                return False
        
        try:
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                return False
            
            # Generate filename
            filename = self.sanitize_filename(doc['title'])
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Create unique filename if exists
            filepath = troubleshooting_folder / filename
            counter = 1
            while filepath.exists():
                name_part = filename.replace('.pdf', '')
                filepath = troubleshooting_folder / f"{name_part}_{counter}.pdf"
                counter += 1
            
            # Save PDF
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Update document info
            doc['downloaded'] = True
            doc['local_path'] = str(filepath)
            doc['file_size'] = os.path.getsize(filepath)
            
            self.download_count += 1
            self.save_progress()
            
            print(f"    ✅ [{self.download_count}] {filepath.name[:65]}")
            
            # Add to catalog
            self.pdf_catalog.append({
                'filename': filepath.name,
                'path': str(filepath),
                'title': doc['title'],
                'url': doc['url'],
                'boiler_type': doc['boiler_type'],
                'category': 'Troubleshooting',
                'file_size_mb': round(doc['file_size'] / (1024*1024), 2),
                'download_date': datetime.now().isoformat()
            })
            
            return True
            
        except Exception:
            return False
    
    def download_troubleshooting_pdfs(self, boiler_data: Dict):
        """Download ONLY troubleshooting PDFs for a boiler"""
        boiler_type = boiler_data['asset_subtype']
        models = boiler_data['models']
        manufacturers = boiler_data['manufacturers']
        
        print(f"\n{'='*100}")
        print(f"🔧 {boiler_type}")
        print(f"📋 Models: {models}")
        print(f"🏢 Manufacturers: {manufacturers}")
        print(f"{'='*100}")
        
        # Get troubleshooting folder
        boiler_folder = self.base_dir / self.get_folder_name(boiler_type)
        troubleshooting_folder = boiler_folder / 'troubleshooting'
        troubleshooting_folder.mkdir(parents=True, exist_ok=True)
        
        # Parse models and manufacturers
        model_list = [m.strip() for m in models.split(',')]
        manufacturer_list = [m.strip() for m in manufacturers.split(',')]
        
        print(f"\n📂 TROUBLESHOOTING RESOURCES ONLY")
        
        # Comprehensive troubleshooting queries
        troubleshooting_queries = []
        
        # Model-specific queries
        for model in model_list:
            troubleshooting_queries.extend([
                f"{model} troubleshooting guide PDF",
                f"{model} maintenance manual troubleshooting",
                f"{model} diagnostics handbook PDF",
                f"{model} service manual repair guide",
                f"{model} problem solving guide",
                f"{model} common issues troubleshooting"
            ])
        
        # Manufacturer-specific queries
        for mfr in manufacturer_list:
            troubleshooting_queries.extend([
                f"{mfr} {boiler_type} troubleshooting manual",
                f"{mfr} troubleshooting procedures guide",
                f"{mfr} maintenance troubleshooting PDF",
                f"{mfr} diagnostic procedures manual"
            ])
        
        # Generic boiler type queries
        troubleshooting_queries.extend([
            f"{boiler_type} troubleshooting diagnostics guide",
            f"{boiler_type} maintenance troubleshooting procedures",
            f"{boiler_type} operation troubleshooting manual",
            f"{boiler_type} problem diagnosis guide",
            f"{boiler_type} fault finding manual PDF",
            f"{boiler_type} repair troubleshooting handbook",
            f"{boiler_type} service troubleshooting guide",
            f"{boiler_type} operational problems solutions"
        ])
        
        # Execute searches and downloads
        for query in troubleshooting_queries:
            pdf_docs = self.search_pdf_documents(query, boiler_type, num_results=20)
            for doc in pdf_docs:
                self.download_pdf(doc, troubleshooting_folder)
                time.sleep(0.8)
        
        print(f"\n✅ Completed: {boiler_type}")
        pdfs_downloaded = len([p for p in self.pdf_catalog if p['boiler_type'] == boiler_type])
        print(f"   Troubleshooting PDFs Downloaded: {pdfs_downloaded}")
    
    def save_final_catalog(self):
        """Save catalog"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        catalog_file = self.base_dir / f"troubleshooting_catalog_{timestamp}.csv"
        if self.pdf_catalog:
            df_catalog = pd.DataFrame(self.pdf_catalog)
            df_catalog.to_csv(catalog_file, index=False, encoding='utf-8')
            print(f"\n✅ Catalog: {catalog_file}")
        
        catalog_json = self.base_dir / f"troubleshooting_catalog_{timestamp}.json"
        with open(catalog_json, 'w', encoding='utf-8') as f:
            json.dump(self.pdf_catalog, f, indent=2, ensure_ascii=False)
        
        if self.failed_downloads:
            failed_file = self.base_dir / f"troubleshooting_failed_{timestamp}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_downloads, f, indent=2)
        
        return catalog_file
    
    def generate_report(self):
        """Generate report"""
        print(f"\n{'='*100}")
        print(f"📊 TROUBLESHOOTING DOWNLOAD REPORT")
        print(f"{'='*100}")
        
        print(f"\n📈 Statistics:")
        print(f"  • Total Searches: {self.search_count}")
        print(f"  • PDFs Found: {len(self.results)}")
        print(f"  • PDFs Downloaded: {self.download_count}")
        print(f"  • Failed: {len(self.failed_downloads)}")
        
        total_size = sum([item['file_size_mb'] for item in self.pdf_catalog])
        print(f"  • Total Size: {total_size:.2f} MB")
        
        boiler_counts = {}
        for item in self.pdf_catalog:
            bt = item['boiler_type']
            boiler_counts[bt] = boiler_counts.get(bt, 0) + 1
        
        print(f"\n📋 Troubleshooting PDFs by Boiler:")
        for bt, count in boiler_counts.items():
            print(f"  • {bt}: {count} PDFs")


def main():
    """Main execution - TROUBLESHOOTING ONLY for 2 boilers"""
    
    EXA_API_KEY = '2afc3264-d175-4274-a613-366aeab68372'
    
    print("\n🔧 TROUBLESHOOTING PDF DOWNLOADER")
    print("=" * 100)
    print("🎯 Target: BFB & Waste Heat Recovery Boiler - Troubleshooting Category ONLY")
    print("=" * 100)
    
    downloader = TroubleshootingOnlyDownloader(EXA_API_KEY, base_dir="downloaded_data")
    
    # Only these 2 boiler types
    target_boilers = [
        {
            'asset_subtype': 'BFB (Bubbling Fluidized Bed)',
            'models': 'Valmet BFB, Andritz PowerFluid, Sumitomo SHI FW',
            'manufacturers': 'Valmet, Andritz, Sumitomo'
        },
        {
            'asset_subtype': 'Waste Heat Recovery Boiler',
            'models': 'Thermax WHRS, Cleaver-Brooks CRB, AC Boilers WHR',
            'manufacturers': 'Thermax, Cleaver-Brooks, AC Boilers'
        }
    ]
    
    print(f"\n📊 Will download troubleshooting PDFs for:")
    for b in target_boilers:
        print(f"  • {b['asset_subtype']}")
    
    print(f"\n⚙️  Configuration:")
    print(f"   - Category: TROUBLESHOOTING ONLY")
    print(f"   - 20 results per search")
    print(f"   - 20+ queries per boiler")
    print(f"   - Estimated: 50-100 PDFs per boiler")
    print(f"   - Total estimated: 100-200 troubleshooting PDFs")
    print(f"   - Time: 20-30 minutes")
    
    input("\n Press ENTER to start downloading troubleshooting PDFs... ")
    
    # Download for both boilers
    for boiler in target_boilers:
        downloader.download_troubleshooting_pdfs(boiler)
    
    # Generate report
    downloader.generate_report()
    
    # Save catalog
    catalog_file = downloader.save_final_catalog()
    
    print(f"\n🎉 TROUBLESHOOTING DOWNLOAD COMPLETE!")
    print(f"📁 PDFs saved to:")
    print(f"   - downloaded_data/bfb_bubbling_fluidized_bed/troubleshooting/")
    print(f"   - downloaded_data/waste_heat_recovery_boiler/troubleshooting/")
    print(f"📋 Catalog: {catalog_file}")


if __name__ == "__main__":
    main()