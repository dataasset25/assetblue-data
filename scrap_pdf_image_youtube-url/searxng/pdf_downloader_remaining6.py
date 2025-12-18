"""
Industrial Boiler PDF Documentation Downloader - REMAINING 6 BOILER TYPES ONLY
This script only processes the 6 boiler types that haven't been downloaded yet
SSL verification disabled for problematic sites
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

class Remaining6BoilerPDFDownloader:
    def __init__(self, exa_api_key: str, base_dir: str = "downloaded_data"):
        """Initialize PDF downloader for remaining 6 boiler types"""
        self.exa = Exa(exa_api_key)
        self.base_dir = Path(base_dir)
        self.progress_file = self.base_dir / "download_progress_remaining6.json"
        
        self.results = []
        self.pdf_catalog = []
        self.search_count = 0
        self.download_count = 0
        self.failed_downloads = []
        self.progress_data = {
            'start_time': datetime.now().isoformat(),
            'current_boiler': None,
            'completed_boilers': [],
            'total_searches': 0,
            'total_downloads': 0,
            'total_failures': 0
        }
        
        # Create base directory
        self.base_dir.mkdir(exist_ok=True)
        self.save_progress()
    
    def get_folder_name(self, boiler_type: str) -> str:
        """Convert boiler type to folder name"""
        folder_map = {
            'Stoker-Fired Boiler': 'stoker_fired_boiler',
            'Pulverized Coal (PC) Boiler': 'pulverized_coal_pc_boiler',
            'Biomass Boiler': 'biomass_boiler',
            'Electric Boiler': 'electric_boiler',
            'Condensing Boiler': 'condensing_boiler',
            'Modular Boiler System': 'modular_boiler_system'
        }
        return folder_map.get(boiler_type, boiler_type.lower().replace(' ', '_'))
    
    def setup_boiler_directories(self, boiler_type: str) -> Dict[str, Path]:
        """Create directory structure for specific boiler type"""
        boiler_folder = self.base_dir / self.get_folder_name(boiler_type)
        boiler_folder.mkdir(exist_ok=True)
        
        # Create category subfolders
        category_folders = {
            'failure': boiler_folder / 'failure',
            'technical': boiler_folder / 'technical',
            'troubleshooting': boiler_folder / 'troubleshooting',
            'product': boiler_folder / 'product'
        }
        
        for folder in category_folders.values():
            folder.mkdir(exist_ok=True)
        
        return category_folders
    
    def save_progress(self):
        """Save real-time progress to JSON file"""
        self.progress_data['last_update'] = datetime.now().isoformat()
        self.progress_data['total_searches'] = self.search_count
        self.progress_data['total_downloads'] = self.download_count
        self.progress_data['total_failures'] = len(self.failed_downloads)
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
    
    def search_pdf_documents(self, query: str, category: str, boiler_type: str, 
                            num_results: int = 20) -> List[Dict]:
        """Search for maximum PDF documents using Exa"""
        try:
            print(f"  🔍 Searching PDFs: {query[:70]}...")
            
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
                        'category': category,
                        'query': query,
                        'title': item.title,
                        'url': item.url,
                        'score': getattr(item, 'score', 'N/A'),
                        'published_date': getattr(item, 'published_date', 'N/A'),
                        'author': getattr(item, 'author', 'N/A'),
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
        """Create safe filename from title"""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace(' ', '_')
        if len(filename) > max_length:
            filename = filename[:max_length]
        return filename
    
    def download_pdf(self, doc: Dict, category_folder: Path) -> bool:
        """Download a single PDF document with retry logic"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                url = doc['url']
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/x-pdf,*/*'
                }
                
                # Disable SSL verification to avoid certificate errors
                response = requests.get(url, headers=headers, timeout=15, stream=True, verify=False)
                response.raise_for_status()
                break  # Success, exit retry loop
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    # Silent fail - just log and continue
                    self.failed_downloads.append({
                        'url': doc['url'],
                        'title': doc['title'],
                        'boiler_type': doc['boiler_type'],
                        'category': doc['category'],
                        'reason': f'Connection error: {str(e)[:50]}'
                    })
                    self.save_progress()
                    return False
            except requests.exceptions.RequestException as e:
                # Silent fail for other errors
                self.failed_downloads.append({
                    'url': doc['url'],
                    'title': doc['title'],
                    'boiler_type': doc['boiler_type'],
                    'category': doc['category'],
                    'reason': str(e)[:100]
                })
                self.save_progress()
                return False
        
        try:
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                # Silent skip - not a PDF
                return False
            
            # Generate filename
            filename = self.sanitize_filename(doc['title'])
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Create unique filename if exists
            filepath = category_folder / filename
            counter = 1
            while filepath.exists():
                name_part = filename.replace('.pdf', '')
                filepath = category_folder / f"{name_part}_{counter}.pdf"
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
            
            # Only print every 10th download to reduce clutter
            if self.download_count % 10 == 0 or self.download_count <= 5:
                print(f"    ✅ [{self.download_count}] Saved: {filepath.name[:60]}")
            elif self.download_count % 10 == 1:
                print(f"    ... downloading (#{self.download_count})")
            
            # Add to catalog
            self.pdf_catalog.append({
                'filename': filepath.name,
                'path': str(filepath),
                'title': doc['title'],
                'url': doc['url'],
                'boiler_type': doc['boiler_type'],
                'category': doc['category'],
                'file_size_mb': round(doc['file_size'] / (1024*1024), 2),
                'download_date': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.failed_downloads.append({
                'url': doc['url'],
                'title': doc['title'],
                'boiler_type': doc['boiler_type'],
                'category': doc['category'],
                'reason': str(e)[:100]
            })
            self.save_progress()
            return False
    
    def scrape_boiler_pdfs_maximum(self, boiler_data: Dict):
        """Scrape MAXIMUM PDFs for a specific boiler type"""
        boiler_type = boiler_data['asset_subtype']
        models = boiler_data['models']
        manufacturers = boiler_data['manufacturers']
        
        # Update progress
        self.progress_data['current_boiler'] = boiler_type
        self.save_progress()
        
        print(f"\n{'='*100}")
        print(f"🏭 [{boiler_data['id']}] {boiler_type}")
        print(f"📋 Models: {models}")
        print(f"🏢 Manufacturers: {manufacturers}")
        print(f"{'='*100}")
        
        # Setup directories
        category_folders = self.setup_boiler_directories(boiler_type)
        
        # Parse models and manufacturers
        model_list = [m.strip() for m in models.split(',')]
        manufacturer_list = [m.strip() for m in manufacturers.split(',')]
        
        # CATEGORY 1: FAILURE CASES
        print(f"\n📂 Category: FAILURE CASES (failure/)")
        failure_queries = []
        
        for model in model_list:
            failure_queries.extend([
                f"{model} failure analysis PDF",
                f"{model} boiler tube failure case study",
                f"{model} incident report investigation",
                f"{model} root cause analysis failure"
            ])
        
        for mfr in manufacturer_list:
            failure_queries.extend([
                f"{mfr} {boiler_type} failure case study",
                f"{mfr} boiler failure modes effects analysis"
            ])
        
        failure_queries.extend([
            f"{boiler_type} failure analysis research paper",
            f"{boiler_type} tube failure investigation report",
            f"{boiler_type} common failures troubleshooting"
        ])
        
        for query in failure_queries:
            pdf_docs = self.search_pdf_documents(query, "Failure Cases", boiler_type, num_results=20)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['failure'])
                time.sleep(0.8)
        
        # CATEGORY 2: TECHNICAL MANUALS
        print(f"\n📂 Category: TECHNICAL MANUALS (technical/)")
        technical_queries = []
        
        for model in model_list:
            technical_queries.extend([
                f"{model} technical manual PDF",
                f"{model} design specifications datasheet",
                f"{model} engineering documentation",
                f"{model} technical reference guide"
            ])
        
        for mfr in manufacturer_list:
            technical_queries.extend([
                f"{mfr} {boiler_type} technical manual",
                f"{mfr} boiler specifications PDF",
                f"{mfr} engineering data book"
            ])
        
        technical_queries.extend([
            f"{boiler_type} design manual PDF",
            f"{boiler_type} technical specifications handbook",
            f"{boiler_type} engineering reference material"
        ])
        
        for query in technical_queries:
            pdf_docs = self.search_pdf_documents(query, "Technical Manuals", boiler_type, num_results=20)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['technical'])
                time.sleep(0.8)
        
        # CATEGORY 3: TROUBLESHOOTING RESOURCES
        print(f"\n📂 Category: TROUBLESHOOTING (troubleshooting/)")
        troubleshooting_queries = []
        
        for model in model_list:
            troubleshooting_queries.extend([
                f"{model} troubleshooting guide PDF",
                f"{model} maintenance manual procedures",
                f"{model} diagnostics handbook",
                f"{model} service manual repair"
            ])
        
        for mfr in manufacturer_list:
            troubleshooting_queries.extend([
                f"{mfr} {boiler_type} troubleshooting manual",
                f"{mfr} maintenance procedures guide"
            ])
        
        troubleshooting_queries.extend([
            f"{boiler_type} troubleshooting diagnostics guide",
            f"{boiler_type} maintenance best practices",
            f"{boiler_type} operation troubleshooting manual"
        ])
        
        for query in troubleshooting_queries:
            pdf_docs = self.search_pdf_documents(query, "Troubleshooting", boiler_type, num_results=20)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['troubleshooting'])
                time.sleep(0.8)
        
        # CATEGORY 4: PRODUCT DOCUMENTATION
        print(f"\n📂 Category: PRODUCT DOCUMENTATION (product/)")
        product_queries = []
        
        for model in model_list:
            product_queries.extend([
                f"{model} product manual PDF",
                f"{model} installation guide commissioning",
                f"{model} operation maintenance manual",
                f"{model} user guide documentation"
            ])
        
        for mfr in manufacturer_list:
            product_queries.extend([
                f"{mfr} {boiler_type} product catalog",
                f"{mfr} installation commissioning manual",
                f"{mfr} operation maintenance guide"
            ])
        
        product_queries.extend([
            f"{boiler_type} product specifications brochure",
            f"{boiler_type} installation manual PDF",
            f"{boiler_type} operation maintenance documentation"
        ])
        
        for query in product_queries:
            pdf_docs = self.search_pdf_documents(query, "Product Documentation", boiler_type, num_results=20)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['product'])
                time.sleep(0.8)
        
        # Mark boiler as completed
        self.progress_data['completed_boilers'].append(boiler_type)
        self.save_progress()
        
        print(f"\n✅ Completed: {boiler_type}")
        print(f"   Downloaded: {len([p for p in self.pdf_catalog if p['boiler_type'] == boiler_type])} PDFs")
    
    def save_final_catalog(self):
        """Save final comprehensive catalog"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save PDF catalog
        catalog_file = self.base_dir / f"pdf_catalog_remaining6_{timestamp}.csv"
        if self.pdf_catalog:
            df_catalog = pd.DataFrame(self.pdf_catalog)
            df_catalog.to_csv(catalog_file, index=False, encoding='utf-8')
            print(f"\n✅ PDF Catalog: {catalog_file}")
        
        # Save JSON catalog
        catalog_json = self.base_dir / f"pdf_catalog_remaining6_{timestamp}.json"
        with open(catalog_json, 'w', encoding='utf-8') as f:
            json.dump(self.pdf_catalog, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON Catalog: {catalog_json}")
        
        # Save search results
        results_file = self.base_dir / f"search_results_remaining6_{timestamp}.csv"
        if self.results:
            df_results = pd.DataFrame(self.results)
            df_results.to_csv(results_file, index=False, encoding='utf-8')
            print(f"✅ Search Results: {results_file}")
        
        # Save failed downloads
        if self.failed_downloads:
            failed_file = self.base_dir / f"failed_downloads_remaining6_{timestamp}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_downloads, f, indent=2, ensure_ascii=False)
            print(f"⚠️  Failed Downloads: {failed_file}")
        
        return catalog_file
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n{'='*100}")
        print(f"📊 FINAL DOWNLOAD REPORT - REMAINING 6 BOILER TYPES")
        print(f"{'='*100}")
        
        print(f"\n📈 Overall Statistics:")
        print(f"  • Total Searches: {self.search_count}")
        print(f"  • PDFs Found: {len(self.results)}")
        print(f"  • PDFs Downloaded: {self.download_count}")
        print(f"  • Failed Downloads: {len(self.failed_downloads)}")
        print(f"  • Success Rate: {(self.download_count/len(self.results)*100 if self.results else 0):.1f}%")
        
        total_size_mb = sum([item['file_size_mb'] for item in self.pdf_catalog])
        print(f"  • Total Size: {total_size_mb:.2f} MB")
        
        # By boiler type
        boiler_counts = {}
        for item in self.pdf_catalog:
            bt = item['boiler_type']
            boiler_counts[bt] = boiler_counts.get(bt, 0) + 1
        
        print(f"\n📋 PDFs by Boiler Type:")
        for bt, count in sorted(boiler_counts.items()):
            print(f"  • {bt}: {count} PDFs")
        
        # By category
        category_counts = {}
        for item in self.pdf_catalog:
            cat = item['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print(f"\n📂 PDFs by Category:")
        for cat, count in sorted(category_counts.items()):
            print(f"  • {cat}: {count} PDFs")


def load_remaining_6_boilers():
    """Load ONLY the remaining 6 boiler types that weren't downloaded"""
    return [
        {
            'id': 10,
            'asset_subtype': 'Stoker-Fired Boiler',
            'models': 'Detroit DTS, Riley Power TSG, B&W Sterling',
            'manufacturers': 'Detroit Stoker, Riley Power, B&W'
        },
        {
            'id': 11,
            'asset_subtype': 'Pulverized Coal (PC) Boiler',
            'models': 'B&W Carolina, CE Tangential, Foster Wheeler Arch',
            'manufacturers': 'B&W, Combustion Engineering, Foster Wheeler'
        },
        {
            'id': 12,
            'asset_subtype': 'Biomass Boiler',
            'models': 'DP CleanTech, Valmet CYMIC, B&W Vølund',
            'manufacturers': 'DP CleanTech, Valmet, B&W Vølund'
        },
        {
            'id': 13,
            'asset_subtype': 'Electric Boiler',
            'models': 'Fulton FB-E, Chromalox CES, Precision MPB',
            'manufacturers': 'Fulton, Chromalox, Precision Boilers'
        },
        {
            'id': 14,
            'asset_subtype': 'Condensing Boiler',
            'models': 'Viessmann Vitodens, Buderus GB, Bosch Condens',
            'manufacturers': 'Viessmann, Buderus, Bosch'
        },
        {
            'id': 15,
            'asset_subtype': 'Modular Boiler System',
            'models': 'Lochinvar CREST, Aerco Benchmark, RBI Torus',
            'manufacturers': 'Lochinvar, Aerco, RBI'
        }
    ]


def main():
    """Main execution function - ONLY REMAINING 6 BOILERS"""
    
    EXA_API_KEY = '2afc3264-d175-4274-a613-366aeab68372'
    
    print("\n🚀 PDF DOWNLOADER - REMAINING 6 BOILER TYPES ONLY")
    print("=" * 100)
    print("⚠️  This will NOT touch your existing 9 downloaded boiler types!")
    print("=" * 100)
    
    downloader = Remaining6BoilerPDFDownloader(EXA_API_KEY, base_dir="downloaded_data")
    
    # Load ONLY the remaining 6 boiler types
    boiler_dataset = load_remaining_6_boilers()
    
    print(f"\n📊 Processing ONLY these 6 boiler types:")
    for b in boiler_dataset:
        print(f"  {b['id']}. {b['asset_subtype']}")
    
    print(f"\n📁 Base directory: {downloader.base_dir}/")
    print(f"📊 Real-time progress: {downloader.progress_file}")
    
    print("\n⚙️  Configuration:")
    print("   - 20 results per search query")
    print("   - 15+ queries per category")
    print("   - 4 categories per boiler type")
    print("   - Estimated: 100-150 PDFs per boiler type")
    print(f"   - Total estimated: 600-900 PDFs for these 6 boilers")
    print("\n⏱️  Estimated time: 1-2 hours")
    
    input("\n Press ENTER to start downloading remaining 6 boiler types... ")
    
    # Process only the 6 remaining boiler types
    for boiler in boiler_dataset:
        downloader.scrape_boiler_pdfs_maximum(boiler)
    
    # Generate final report
    downloader.generate_final_report()
    
    # Save catalogs
    catalog_file = downloader.save_final_catalog()
    
    print(f"\n🎉 REMAINING 6 BOILERS DOWNLOAD COMPLETE!")
    print(f"📁 All PDFs saved to: {downloader.base_dir}/")
    print(f"📋 New Catalog: {catalog_file}")
    print(f"📊 Progress Log: {downloader.progress_file}")
    print(f"\n✅ Your existing 9 boiler types remain untouched!")


if __name__ == "__main__":
    main()