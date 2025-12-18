"""
Extract All PDF URLs from Downloaded Collection
Combines all catalog files and extracts unique URLs for all 1,200+ PDFs
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import glob

class URLExtractor:
    def __init__(self, base_dir: str = "downloaded_data"):
        """Initialize URL extractor"""
        self.base_dir = Path(base_dir)
        self.all_urls = []
        self.all_documents = []
        
    def find_all_catalogs(self):
        """Find all catalog CSV files"""
        catalog_patterns = [
            "pdf_catalog_*.csv",
            "pdf_catalog_remaining6_*.csv",
            "troubleshooting_catalog_*.csv"
        ]
        
        catalog_files = []
        for pattern in catalog_patterns:
            files = list(self.base_dir.glob(pattern))
            catalog_files.extend(files)
        
        # Remove duplicates
        catalog_files = list(set(catalog_files))
        
        print(f"\n📂 Found {len(catalog_files)} catalog files:")
        for f in catalog_files:
            print(f"  • {f.name}")
        
        return catalog_files
    
    def extract_urls_from_catalogs(self, catalog_files):
        """Extract URLs from all catalog files"""
        all_data = []
        
        for catalog_file in catalog_files:
            try:
                print(f"\n📖 Reading: {catalog_file.name}")
                df = pd.read_csv(catalog_file)
                
                print(f"  ✅ Found {len(df)} entries")
                all_data.append(df)
                
            except Exception as e:
                print(f"  ❌ Error reading {catalog_file.name}: {str(e)}")
        
        if not all_data:
            print("\n⚠️  No data found in catalogs!")
            return pd.DataFrame()
        
        # Combine all catalogs
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n📊 Total entries before deduplication: {len(combined_df)}")
        
        # Remove duplicates based on URL
        combined_df = combined_df.drop_duplicates(subset=['url'], keep='first')
        print(f"📊 Unique entries after deduplication: {len(combined_df)}")
        
        return combined_df
    
    def organize_urls(self, df):
        """Organize URLs by boiler type and category"""
        organized = {}
        
        for boiler_type in df['boiler_type'].unique():
            boiler_data = df[df['boiler_type'] == boiler_type]
            organized[boiler_type] = {}
            
            for category in boiler_data['category'].unique():
                category_data = boiler_data[boiler_data['category'] == category]
                urls = category_data['url'].tolist()
                organized[boiler_type][category] = {
                    'count': len(urls),
                    'urls': urls
                }
        
        return organized
    
    def save_all_formats(self, df, organized):
        """Save URLs in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Simple text file - All URLs (one per line)
        all_urls_file = self.base_dir / f"ALL_PDF_URLS_{timestamp}.txt"
        with open(all_urls_file, 'w', encoding='utf-8') as f:
            f.write(f"# All PDF URLs - Total: {len(df)}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for url in df['url'].tolist():
                f.write(f"{url}\n")
        print(f"\n✅ All URLs (TXT): {all_urls_file}")
        
        # 2. CSV with full details
        detailed_csv = self.base_dir / f"ALL_PDF_DETAILS_{timestamp}.csv"
        df_export = df[['url', 'title', 'boiler_type', 'category', 'file_size_mb', 'filename']].copy()
        df_export.to_csv(detailed_csv, index=False, encoding='utf-8')
        print(f"✅ Detailed CSV: {detailed_csv}")
        
        # 3. JSON organized by boiler type
        organized_json = self.base_dir / f"URLS_BY_BOILER_{timestamp}.json"
        with open(organized_json, 'w', encoding='utf-8') as f:
            json.dump(organized, f, indent=2, ensure_ascii=False)
        print(f"✅ Organized JSON: {organized_json}")
        
        # 4. Markdown format for easy reading
        markdown_file = self.base_dir / f"ALL_URLS_{timestamp}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(f"# Industrial Boiler PDF URLs Collection\n\n")
            f.write(f"**Total PDFs:** {len(df)}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"---\n\n")
            
            for boiler_type in sorted(organized.keys()):
                f.write(f"## {boiler_type}\n\n")
                
                for category in sorted(organized[boiler_type].keys()):
                    data = organized[boiler_type][category]
                    f.write(f"### {category} ({data['count']} PDFs)\n\n")
                    
                    for idx, url in enumerate(data['urls'], 1):
                        # Get title for this URL
                        title_row = df[df['url'] == url]
                        if not title_row.empty:
                            title = title_row.iloc[0]['title']
                            f.write(f"{idx}. [{title}]({url})\n")
                        else:
                            f.write(f"{idx}. {url}\n")
                    f.write(f"\n")
        print(f"✅ Markdown: {markdown_file}")
        
        # 5. Excel with multiple sheets
        excel_file = self.base_dir / f"ALL_URLS_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for boiler_type in organized.keys():
                for category in organized[boiler_type].keys():
                    summary_data.append({
                        'Boiler Type': boiler_type,
                        'Category': category,
                        'PDF Count': organized[boiler_type][category]['count']
                    })
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # All URLs sheet
            df_export.to_excel(writer, sheet_name='All URLs', index=False)
            
            # By category sheets
            for category in df['category'].unique():
                category_df = df[df['category'] == category][['url', 'title', 'boiler_type', 'filename']]
                sheet_name = category[:31]  # Excel sheet name limit
                category_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ Excel: {excel_file}")
        
        return all_urls_file, detailed_csv, organized_json, markdown_file, excel_file
    
    def generate_statistics(self, df, organized):
        """Generate comprehensive statistics"""
        print(f"\n{'='*100}")
        print(f"📊 URL EXTRACTION REPORT")
        print(f"{'='*100}")
        
        print(f"\n📈 Overall Statistics:")
        print(f"  • Total Unique URLs: {len(df)}")
        print(f"  • Total File Size: {df['file_size_mb'].sum():.2f} MB")
        print(f"  • Average File Size: {df['file_size_mb'].mean():.2f} MB")
        print(f"  • Largest PDF: {df['file_size_mb'].max():.2f} MB")
        print(f"  • Smallest PDF: {df['file_size_mb'].min():.2f} MB")
        
        print(f"\n📋 URLs by Boiler Type:")
        for boiler_type, data in sorted(organized.items()):
            total_urls = sum(cat_data['count'] for cat_data in data.values())
            print(f"  • {boiler_type}: {total_urls} URLs")
        
        print(f"\n📂 URLs by Category:")
        category_counts = df.groupby('category').size()
        for category, count in category_counts.items():
            print(f"  • {category}: {count} URLs")
        
        print(f"\n🏢 Top Domains:")
        df['domain'] = df['url'].apply(lambda x: x.split('/')[2] if len(x.split('/')) > 2 else 'Unknown')
        top_domains = df['domain'].value_counts().head(10)
        for domain, count in top_domains.items():
            print(f"  • {domain}: {count} PDFs")
        
        print(f"\n📄 File Type Distribution:")
        df['has_pdf_extension'] = df['url'].str.contains('.pdf', case=False)
        pdf_count = df['has_pdf_extension'].sum()
        print(f"  • URLs with .pdf extension: {pdf_count} ({pdf_count/len(df)*100:.1f}%)")
        print(f"  • URLs without .pdf extension: {len(df)-pdf_count} ({(len(df)-pdf_count)/len(df)*100:.1f}%)")


def main():
    """Main execution function"""
    
    print("\n🔗 PDF URL EXTRACTOR")
    print("=" * 100)
    print("📚 Extracting URLs from all downloaded PDF catalogs")
    print("=" * 100)
    
    extractor = URLExtractor(base_dir="downloaded_data")
    
    # Find all catalog files
    catalog_files = extractor.find_all_catalogs()
    
    if not catalog_files:
        print("\n❌ No catalog files found!")
        print("   Make sure you're running this in the directory containing 'downloaded_data' folder")
        return
    
    # Extract URLs
    print(f"\n{'='*100}")
    print("🔍 EXTRACTING URLS FROM CATALOGS")
    print(f"{'='*100}")
    
    combined_df = extractor.extract_urls_from_catalogs(catalog_files)
    
    if combined_df.empty:
        print("\n❌ No URLs found in catalogs!")
        return
    
    # Organize by boiler type and category
    print(f"\n{'='*100}")
    print("📊 ORGANIZING URLS")
    print(f"{'='*100}")
    
    organized = extractor.organize_urls(combined_df)
    
    # Save in multiple formats
    print(f"\n{'='*100}")
    print("💾 SAVING URLs IN MULTIPLE FORMATS")
    print(f"{'='*100}")
    
    files = extractor.save_all_formats(combined_df, organized)
    
    # Generate statistics
    extractor.generate_statistics(combined_df, organized)
    
    # Final summary
    print(f"\n{'='*100}")
    print("🎉 URL EXTRACTION COMPLETE!")
    print(f"{'='*100}")
    
    print(f"\n📁 Output Files Created:")
    print(f"  1. {files[0].name} - All URLs (plain text)")
    print(f"  2. {files[1].name} - Detailed CSV with metadata")
    print(f"  3. {files[2].name} - Organized JSON by boiler type")
    print(f"  4. {files[3].name} - Formatted Markdown")
    print(f"  5. {files[4].name} - Excel with multiple sheets")
    
    print(f"\n💡 Quick Stats:")
    print(f"  • Total Unique URLs: {len(combined_df)}")
    print(f"  • Boiler Types: {combined_df['boiler_type'].nunique()}")
    print(f"  • Categories: {combined_df['category'].nunique()}")
    print(f"  • Total Size: {combined_df['file_size_mb'].sum():.2f} MB")
    
    print(f"\n✅ All URL files saved in: downloaded_data/")


if __name__ == "__main__":
    main()