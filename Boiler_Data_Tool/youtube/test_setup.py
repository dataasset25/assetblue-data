#!/usr/bin/env python3
"""
Test script to verify Oxylabs proxy setup and yt-dlp installation
"""

import subprocess
import sys
import requests
import random

def test_yt_dlp():
    """Test if yt-dlp is installed and working."""
    try:
        # Try direct command first
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, check=True)
        print(f"✓ yt-dlp is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Try Python module approach
            result = subprocess.run(["python", "-m", "yt_dlp", "--version"], capture_output=True, text=True, check=True)
            print(f"✓ yt-dlp is installed (via Python module): {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ yt-dlp is not installed or not working")
            print("  Install with: pip install yt-dlp")
            return False

def test_config():
    """Test if config file exists and has credentials."""
    try:
        from config import OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT, OXYLABS_PORT
        print("✓ config.py found")
        
        if OXYLABS_USERNAME == "YOUR_USERNAME":
            print("✗ Please update OXYLABS_USERNAME in config.py")
            return False
        if OXYLABS_PASSWORD == "YOUR_PASSWORD":
            print("✗ Please update OXYLABS_PASSWORD in config.py")
            return False
        if OXYLABS_ENDPOINT == "your-endpoint":
            print("✗ Please update OXYLABS_ENDPOINT in config.py")
            return False
            
        print("✓ Credentials configured in config.py")
        return True
    except ImportError:
        print("✗ config.py not found")
        return False

def test_proxy_connection():
    """Test proxy connection with a simple request."""
    try:
        from config import OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_ENDPOINT, OXYLABS_PORT
        
        # Generate random session ID
        session_id = random.randint(1, 100000)
        username_with_session = f"{OXYLABS_USERNAME}-{session_id}"
        
        proxy_url = f"http://{username_with_session}:{OXYLABS_PASSWORD}@{OXYLABS_ENDPOINT}:{OXYLABS_PORT}"
        
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        print(f"Testing proxy connection with session: {username_with_session}")
        response = requests.get("https://ip.oxylabs.io/location", proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Proxy connection successful")
            print(f"  IP Location: {response.text}")
            return True
        else:
            print(f"✗ Proxy connection failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Proxy connection test failed: {str(e)}")
        return False

def test_url_file():
    """Test if the URL file exists and has content."""
    try:
        with open("subcritical_drum_boiler/sub_critical_drum_boiler.txt", 'r') as f:
            urls = [line.strip() for line in f if 'youtube.com/watch?v=' in line]
        
        if urls:
            print(f"✓ Found {len(urls)} YouTube URLs in the file")
            return True
        else:
            print("✗ No YouTube URLs found in the file")
            return False
    except FileNotFoundError:
        print("✗ URL file not found: subcritical_drum_boiler/sub_critical_drum_boiler.txt")
        return False

def main():
    """Run all tests."""
    print("YouTube Downloader Setup Test")
    print("=" * 40)
    
    tests = [
        ("yt-dlp Installation", test_yt_dlp),
        ("Configuration File", test_config),
        ("URL File", test_url_file),
        ("Proxy Connection", test_proxy_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 20)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    print("=" * 40)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to download videos.")
        print("Run: python youtube_downloader.py")
    else:
        print("\n❌ Some tests failed. Please fix the issues above before running the downloader.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
