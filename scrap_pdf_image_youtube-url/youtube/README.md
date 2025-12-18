# YouTube Video Downloader with Oxylabs Proxy

This script downloads YouTube videos using Oxylabs high-bandwidth proxies to avoid rate limiting and IP blocking.

## Features

- Downloads YouTube videos using Oxylabs high-bandwidth proxies
- Automatic session rotation for better success rates
- Retry mechanism for failed downloads
- Downloads video metadata and thumbnails
- Organizes videos by category (Failure Case, Technical/Manual, Troubleshooting/Maintenance, Product/Documentation/Educational)
- Saves failed download URLs for retry

## Setup Instructions

### 1. Install Dependencies

Run the setup script:
```bash
setup_and_run.bat
```

Or manually install:
```bash
pip install -r requirements.txt
```

### 2. Configure Oxylabs Credentials

Edit `config.py` and replace the placeholder values with your actual Oxylabs credentials:

```python
OXYLABS_USERNAME = "your-actual-username"
OXYLABS_PASSWORD = "your-actual-password"  
OXYLABS_ENDPOINT = "your-actual-endpoint"  # e.g., "pr.oxylabs.io"
OXYLABS_PORT = 60000
```

**Important**: Get your actual credentials from your Oxylabs dashboard. The endpoint should be provided by Oxylabs support.

### 3. Run the Downloader

```bash
python youtube_downloader.py
```

## How It Works

1. **URL Extraction**: Reads YouTube URLs from `subcritical_drum_boiler/sub_critical_drum_boiler.txt`
2. **Proxy Configuration**: Uses Oxylabs high-bandwidth proxies with random session IDs for load balancing
3. **Download Process**: Downloads videos using `yt-dlp` with proxy support
4. **Organization**: Saves videos to `subcritical_drum_boiler_videos/` directory
5. **Error Handling**: Retries failed downloads and saves failed URLs for manual retry

## Proxy Configuration Details

The script uses Oxylabs high-bandwidth proxies with the following features:

- **Session Rotation**: Each download uses a random session ID (`username-{random_number}`)
- **Load Balancing**: Automatic IP assignment based on session ID
- **High Bandwidth**: Optimized for video downloads
- **Reliability**: Built-in retry mechanism

## Output Structure

```
subcritical_drum_boiler_videos/
├── video1.mp4
├── video1.info.json
├── video1.webp
├── video2.mp4
├── video2.info.json
├── video2.webp
└── failed_downloads.txt
```

## Troubleshooting

### Common Issues

1. **"yt-dlp is not installed"**
   - Run: `pip install yt-dlp`

2. **"config.py file not found"**
   - Make sure `config.py` exists in the same directory
   - Check that you've configured your Oxylabs credentials

3. **Proxy connection errors**
   - Verify your Oxylabs credentials are correct
   - Check that your endpoint is correct
   - Ensure your Oxylabs account has sufficient credits

4. **Download failures**
   - Some videos may be private, deleted, or geo-restricted
   - Check `failed_downloads.txt` for URLs that need manual attention

### Performance Tips

- The script includes delays between downloads to be respectful to YouTube
- Failed downloads are automatically retried up to 3 times
- Each download uses a different proxy session for better success rates

## Video Categories

The script processes videos from these categories:
- **Failure Case**: Videos showing boiler failures and incidents
- **Technical/Manual**: Technical documentation and manuals
- **Troubleshooting/Maintenance**: Maintenance and troubleshooting guides
- **Product/Documentation/Educational**: Product information and educational content

## Security Notes

- Keep your `config.py` file secure and don't share it
- Consider using environment variables for production use
- The script uses HTTPS proxies for secure connections

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your Oxylabs account status and credits
3. Ensure your internet connection is stable
4. Check that the source file contains valid YouTube URLs
