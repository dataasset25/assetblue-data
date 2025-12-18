"""
Industrial Boiler PDF Documentation Downloader - Maximum Coverage
Organized folder structure: downloaded_data/boiler_type/category/
Real-time JSON progress tracking
Maximum PDF downloads per category
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
from urllib.parse import urlparse, unquote
import threading

class MaximumBoilerPDFDownloader:
    def __init__(self, exa_api_key: str, base_dir: str = "downloaded_data"):
        """Initialize PDF downloader with maximum coverage settings"""
        self.exa = Exa(exa_api_key)
        self.base_dir = Path(base_dir)
        self.progress_file = self.base_dir / "download_progress.json"
        
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
            'Subcritical Drum Boiler': 'subcritical_drum_boiler',
            'Supercritical Once-Through': 'supercritical_once_through',
            'Ultra-Supercritical': 'ultra_supercritical',
            'CFB (Circulating Fluidized Bed)': 'cfb_circulating_fluidized_bed',
            'BFB (Bubbling Fluidized Bed)': 'bfb_bubbling_fluidized_bed',
            'HRSG (Heat Recovery Steam Generator)': 'hrsg_heat_recovery_steam_generator',
            'Package Water Tube': 'package_water_tube',
            'Fire Tube Scotch Marine': 'fire_tube_scotch_marine',
            'Waste Heat Recovery Boiler': 'waste_heat_recovery_boiler',
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
            
            # Enhanced query for PDF documents
            pdf_query = f"{query} filetype:pdf"
            
            result = self.exa.search_and_contents(
                pdf_query,
                type="neural",
                num_results=num_results,  # Increased to 20
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
        """Check if URL likely points to a PDF with enhanced detection"""
        url_lower = url.lower()
        
        # Strong PDF indicators
        strong_indicators = ['.pdf', '/pdf/', 'pdf?', 'pdf&', 'pdf#']
        if any(indicator in url_lower for indicator in strong_indicators):
            return True
        
        # Exclude common non-PDF sites
        exclude_sites = [
            'scribd.com', 'slideshare.net', 'researchgate.net', 
            'academia.edu', 'manualslib.com', 'yumpu.com',
            'pdfcoffee.com', 'directindustry.com', 'datapdf.com'
        ]
        if any(site in url_lower for site in exclude_sites):
            return False
        
        # Check for document-related patterns
        doc_patterns = ['document', 'manual', 'specification', 'datasheet', 'catalog']
        if any(pattern in url_lower for pattern in doc_patterns):
            return True
            
        return False
    
    def sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """Create safe filename from title"""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace(' ', '_')
        if len(filename) > max_length:
            filename = filename[:max_length]
        return filename
    
    def download_pdf(self, doc: Dict, category_folder: Path) -> bool:
        """Download a single PDF document with enhanced retry logic and faster timeouts"""
        max_retries = 1  # Reduced retries for faster processing
        timeout = 10     # Reduced timeout
        
        for attempt in range(max_retries):
            try:
                url = doc['url']
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/pdf,application/x-pdf,*/*',
                    'Connection': 'keep-alive'
                }
                
                # First, try a HEAD request to check content type quickly
                try:
                    head_response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
                    content_type = head_response.headers.get('content-type', '').lower()
                    
                    # Skip if clearly not a PDF
                    if 'text/html' in content_type or 'application/json' in content_type:
                        print(f"    ⚠️  Skipping HTML/JSON: {content_type[:30]}")
                        return False
                        
                except:
                    pass  # Continue with full download if HEAD fails
                
                response = requests.get(url, headers=headers, timeout=timeout, stream=True)
                response.raise_for_status()
                break  # Success, exit retry loop
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"    ❌ Timeout: {url[:50]}")
                self.failed_downloads.append({
                    'url': doc['url'],
                    'title': doc['title'],
                    'boiler_type': doc['boiler_type'],
                    'category': doc['category'],
                    'reason': f'Timeout after {timeout}s'
                })
                self.save_progress()
                return False
            except requests.exceptions.RequestException as e:
                print(f"    ❌ Download error: {str(e)[:50]}")
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
            # Enhanced PDF verification
            content_type = response.headers.get('content-type', '').lower()
            
            # Check content type
            if 'text/html' in content_type or 'application/json' in content_type:
                print(f"    ⚠️  Not a PDF: {content_type[:30]}")
                return False
            
            # Check file size (skip very small files)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) < 1024:  # Less than 1KB
                print(f"    ⚠️  File too small: {content_length} bytes")
                return False
            
            # Check first few bytes for PDF signature
            try:
                first_chunk = next(response.iter_content(chunk_size=1024))
                if not first_chunk.startswith(b'%PDF'):
                    print(f"    ⚠️  Not a PDF file (missing PDF signature)")
                    return False
            except:
                pass  # Continue if we can't check signature
            
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
            
            # Save PDF efficiently
            with open(filepath, 'wb') as f:
                # Write the first chunk we already read
                if 'first_chunk' in locals():
                    f.write(first_chunk)
                
                # Write remaining chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Update document info
            doc['downloaded'] = True
            doc['local_path'] = str(filepath)
            doc['file_size'] = os.path.getsize(filepath)
            
            self.download_count += 1
            self.save_progress()
            
            print(f"    ✅ [{self.download_count}] Saved: {filepath.name[:60]}")
            
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
        
        # Model-specific failure queries
        for model in model_list:
            failure_queries.extend([
                f"{model} failure analysis PDF",
                f"{model} boiler tube failure case study",
                f"{model} incident report investigation",
                f"{model} root cause analysis failure"
            ])
        
        # Manufacturer-specific failure queries
        for mfr in manufacturer_list:
            failure_queries.extend([
                f"{mfr} {boiler_type} failure case study",
                f"{mfr} boiler failure modes effects analysis"
            ])
        
        # Generic failure queries
        failure_queries.extend([
            f"{boiler_type} failure analysis research paper",
            f"{boiler_type} tube failure investigation report",
            f"{boiler_type} common failures troubleshooting"
        ])
        
        for query in failure_queries:
            pdf_docs = self.search_pdf_documents(query, "Failure Cases", boiler_type, num_results=15)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['failure'])
                time.sleep(0.3)  # Reduced sleep time
        
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
            pdf_docs = self.search_pdf_documents(query, "Technical Manuals", boiler_type, num_results=15)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['technical'])
                time.sleep(0.3)  # Reduced sleep time
        
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
            pdf_docs = self.search_pdf_documents(query, "Troubleshooting", boiler_type, num_results=15)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['troubleshooting'])
                time.sleep(0.3)  # Reduced sleep time
        
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
            pdf_docs = self.search_pdf_documents(query, "Product Documentation", boiler_type, num_results=15)
            for doc in pdf_docs:
                self.download_pdf(doc, category_folders['product'])
                time.sleep(0.3)  # Reduced sleep time
        
        # Mark boiler as completed
        self.progress_data['completed_boilers'].append(boiler_type)
        self.save_progress()
        
        print(f"\n✅ Completed: {boiler_type}")
        print(f"   Downloaded: {len([p for p in self.pdf_catalog if p['boiler_type'] == boiler_type])} PDFs")
    
    def save_final_catalog(self):
        """Save final comprehensive catalog"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save PDF catalog
        catalog_file = self.base_dir / f"pdf_catalog_{timestamp}.csv"
        if self.pdf_catalog:
            df_catalog = pd.DataFrame(self.pdf_catalog)
            df_catalog.to_csv(catalog_file, index=False, encoding='utf-8')
            print(f"\n✅ PDF Catalog: {catalog_file}")
        
        # Save JSON catalog
        catalog_json = self.base_dir / f"pdf_catalog_{timestamp}.json"
        with open(catalog_json, 'w', encoding='utf-8') as f:
            json.dump(self.pdf_catalog, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON Catalog: {catalog_json}")
        
        # Save search results
        results_file = self.base_dir / f"search_results_{timestamp}.csv"
        if self.results:
            df_results = pd.DataFrame(self.results)
            df_results.to_csv(results_file, index=False, encoding='utf-8')
            print(f"✅ Search Results: {results_file}")
        
        # Save failed downloads
        if self.failed_downloads:
            failed_file = self.base_dir / f"failed_downloads_{timestamp}.json"
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_downloads, f, indent=2, ensure_ascii=False)
            print(f"⚠️  Failed Downloads: {failed_file}")
        
        return catalog_file
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print(f"\n{'='*100}")
        print(f"📊 FINAL DOWNLOAD REPORT")
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
        
        print(f"\n📁 Folder Structure:")
        print(f"  {self.base_dir}/")
        print(f"    ├── download_progress.json")
        print(f"    ├── pdf_catalog_*.csv")
        print(f"    ├── pdf_catalog_*.json")
        for boiler_type in boiler_counts.keys():
            folder_name = self.get_folder_name(boiler_type)
            print(f"    ├── {folder_name}/")
            print(f"    │     ├── failure/")
            print(f"    │     ├── technical/")
            print(f"    │     ├── troubleshooting/")
            print(f"    │     └── product/")


def load_remaining_boiler_dataset():
    """Load dataset for remaining 6 boiler types that need PDFs"""
    return [
        {'id': 10, 'asset_subtype': 'Stoker-Fired Boiler', 'models': 'Detroit DTS, Riley Power TSG, B&W Sterling', 'manufacturers': 'Detroit Stoker, Riley Power, B&W'},
        {'id': 11, 'asset_subtype': 'Pulverized Coal (PC) Boiler', 'models': 'B&W Carolina, CE Tangential, Foster Wheeler Arch', 'manufacturers': 'B&W, Combustion Engineering, Foster Wheeler'},
        {'id': 12, 'asset_subtype': 'Biomass Boiler', 'models': 'DP CleanTech, Valmet CYMIC, B&W Vølund', 'manufacturers': 'DP CleanTech, Valmet, B&W Vølund'},
        {'id': 13, 'asset_subtype': 'Electric Boiler', 'models': 'Fulton FB-E, Chromalox CES, Precision MPB', 'manufacturers': 'Fulton, Chromalox, Precision Boilers'},
        {'id': 14, 'asset_subtype': 'Condensing Boiler', 'models': 'Viessmann Vitodens, Buderus GB, Bosch Condens', 'manufacturers': 'Viessmann, Buderus, Bosch'},
        {'id': 15, 'asset_subtype': 'Modular Boiler System', 'models': 'Lochinvar CREST, Aerco Benchmark, RBI Torus', 'manufacturers': 'Lochinvar, Aerco, RBI'}
    ]


def main():
    """Main execution function"""
    
    EXA_API_KEY = '1030957e-6cf2-4a6a-9ed5-2173cab5b751'
    
    if EXA_API_KEY == 'your-exa-api-key-here':
        print("⚠️  ERROR: Please set your EXA_API_KEY environment variable")
        print("   export EXA_API_KEY='your-actual-key'")
        return
    
    print("\n🚀 PDF DOWNLOADER - Remaining 6 Boiler Types")
    print("=" * 100)
    
    downloader = MaximumBoilerPDFDownloader(EXA_API_KEY, base_dir="downloaded_data")
    
    # Load remaining 6 boiler types
    boiler_dataset = load_remaining_boiler_dataset()
    print(f"📊 Processing REMAINING {len(boiler_dataset)} boiler types")
    print(f"📁 Base directory: {downloader.base_dir}/")
    print(f"📊 Real-time progress: {downloader.progress_file}")
    
    print("\n✅ Already completed (9 boiler types):")
    completed_types = [
        "Subcritical Drum Boiler", "Supercritical Once-Through", "Ultra-Supercritical",
        "CFB (Circulating Fluidized Bed)", "BFB (Bubbling Fluidized Bed)", 
        "HRSG (Heat Recovery Steam Generator)", "Package Water Tube", 
        "Fire Tube Scotch Marine", "Waste Heat Recovery Boiler"
    ]
    for bt in completed_types:
        print(f"   ✓ {bt}")
    
    print(f"\n📋 Remaining to process:")
    for boiler in boiler_dataset:
        print(f"   • {boiler['asset_subtype']}")
    
    print("\n⚙️  Configuration:")
    print("   - 15 results per search query")
    print("   - 15+ queries per category")
    print("   - 4 categories per boiler type")
    print("   - Estimated: 50-100 PDFs per boiler type")
    print(f"   - Total estimated: 300-600 PDFs for remaining boiler types")
    print("\n⚠️  This will take 30-60 minutes!")
    
    input("\n Press ENTER to start maximum download... ")
    
    # Process remaining 6 boiler types
    for boiler in boiler_dataset:
        downloader.scrape_boiler_pdfs_maximum(boiler)
    
    # Generate final report
    downloader.generate_final_report()
    
    # Save catalogs
    catalog_file = downloader.save_final_catalog()
    
    print(f"\n🎉 REMAINING BOILER TYPES PDF DOWNLOAD COMPLETE!")
    print(f"📁 All PDFs saved to: {downloader.base_dir}/")
    print(f"📋 Main Catalog: {catalog_file}")
    print(f"📊 Progress Log: {downloader.progress_file}")
    print(f"\n✅ Total boiler types completed: 15/15")


if __name__ == "__main__":
    main()
