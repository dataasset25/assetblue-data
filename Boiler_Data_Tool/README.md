# Industrial Boiler Data Collection Suite

This repository contains a comprehensive suite of tools for collecting boiler-related data from multiple sources, including images, PDFs, and YouTube videos.

## 📁 Project Structure

### 🔍 boiler_images/
Image URL collection from Bing for various boiler types using keyword-based searches.

**Features:**
- Collects image URLs from Bing search
- Organizes by boiler type and category
- Generates CSV outputs with image metadata

**Main Script:** `collect_bing_image_urls_per_boiler_v2.py`

### 📄 searxng/
PDF document downloader for industrial boiler documentation using the Exa API.

**Features:**
- Downloads PDFs by boiler type and category (Failure Cases, Technical Manuals, Troubleshooting, Product Documentation)
- Progress tracking with real-time JSON updates
- Organizes documents in structured folder hierarchy
- Comprehensive download catalog generation

**Main Script:** `pdf_downloader.py`

**Categories:**
- Failure Cases
- Technical Manuals
- Troubleshooting
- Product Documentation

### 🎥 youtube/
YouTube video downloader with Oxylabs high-bandwidth proxy support to avoid rate limiting.

**Features:**
- Downloads videos with proxy support to avoid IP blocking
- Session rotation for better success rates
- Automatic retry mechanism
- Downloads metadata and thumbnails
- Organizes videos by category

**Main Script:** `youtube_downloader.py`

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip
- Git

### Installation

1. Clone this repository:
```bash
git clone <your-repository-url>
cd work
```

2. Install dependencies for each module:

**For YouTube downloader:**
```bash
cd youtube
pip install -r requirements.txt
```

**For PDF downloader:**
```bash
cd searxng
pip install exa-py pandas requests
```

**For Image URL collector:**
```bash
cd boiler_images
pip install requests beautifulsoup4
```

### Configuration

#### YouTube Downloader (config.py)
Create a `config.py` file in the `youtube/` directory:
```python
OXYLABS_USERNAME = "your-actual-username"
OXYLABS_PASSWORD = "your-actual-password"
OXYLABS_ENDPOINT = "pr.oxylabs.io"
OXYLABS_PORT = 60000
```

#### PDF Downloader
Update the API key in `pdf_downloader.py`:
```python
EXA_API_KEY = 'your-exa-api-key-here'
```

## 📊 Usage

### Collect Image URLs
```bash
cd boiler_images
python collect_bing_image_urls_per_boiler_v2.py
```

### Download PDFs
```bash
cd searxng
python pdf_downloader.py
```

### Download YouTube Videos
```bash
cd youtube
python youtube_downloader.py
```

## 📋 Output Structure

### boiler_images/
- `boiler_keywords/` - Keyword files for each boiler type
- `boiler_image_urls/` - Generated CSV files with image URLs

### searxng/
- `downloaded_data/` - Organized PDF files by boiler type and category
- `download_progress.json` - Real-time progress tracking
- `pdf_catalog_*.csv` - Comprehensive catalog of downloaded PDFs

### youtube/
- `subcritical_drum_boiler_videos/` - Downloaded video files
- `*/` - Category-based organization

## 🔧 Features by Module

### boiler_images
- Multi-page image URL collection
- Deduplication across keywords
- CSV export with metadata
- Category-based organization

### searxng
- Maximum coverage PDF search
- Real-time progress tracking
- Automatic file organization
- Comprehensive cataloging
- Error handling and retry logic

### youtube
- Proxy-based downloading
- Session rotation
- Automatic retries
- Metadata preservation

## ⚠️ Important Notes

- **API Keys**: Keep your API keys secure. Never commit `config.py` files.
- **Rate Limiting**: All scripts include delays to be respectful to APIs and websites.
- **Large Data Files**: The `.gitignore` excludes large data files. Generated outputs are not tracked.

## 📝 License

This project is for educational and research purposes.

## 🤝 Contributing

When contributing:
1. Follow the existing code structure
2. Add appropriate comments
3. Include error handling
4. Test with sample data first

## 📞 Support

For issues or questions:
1. Check the existing documentation in each module
2. Review the troubleshooting sections
3. Ensure all dependencies are installed
4. Verify API keys are configured correctly

