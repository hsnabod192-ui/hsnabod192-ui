"""
Snapchat Video Downloader
Downloads videos from Snapchat without watermarks or restrictions
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path
import argparse
import sys

class SnapchatVideoDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.output_dir = Path("downloads")
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_video_url(self, snapchat_url):
        """
        Extract the actual video URL from Snapchat link
        """
        try:
            response = self.session.get(snapchat_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse the response to find video URL
            if 'video' in response.text or 'mp4' in response.text:
                return self._parse_video_url(response.text)
            else:
                print("❌ Could not find video URL in the page")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching URL: {e}")
            return None
    
    def _parse_video_url(self, html_content):
        """
        Parse HTML to extract video URL
        """
        import re
        
        # Look for video URL patterns
        patterns = [
            r'"videoUrl":"([^"]+)"',
            r'src="([^"]*\.mp4[^"]*)"',
            r'href="([^"]*\.mp4[^"]*)"',
            r'data-url="([^"]*\.mp4[^"]*)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                url = match.group(1)
                # Unescape the URL
                url = url.replace('\\/', '/').replace('\\"', '"')
                return url
        
        return None
    
    def download_video(self, video_url, filename=None):
        """
        Download video from URL without watermark
        """
        if not video_url:
            print("❌ Invalid video URL")
            return False
        
        try:
            print(f"⏳ Downloading video from: {video_url}")
            
            response = self.session.get(
                video_url, 
                headers=self.headers, 
                timeout=30,
                stream=True
            )
            response.raise_for_status()
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapchat_video_{timestamp}.mp4"
            
            file_path = self.output_dir / filename
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            print(f"⏳ Progress: {progress:.1f}%", end='\r')
            
            print(f"\n✅ Video downloaded successfully!")
            print(f"📁 Saved to: {file_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Download error: {e}")
            return False
        except IOError as e:
            print(f"❌ File error: {e}")
            return False
    
    def download_from_link(self, snapchat_link, output_filename=None):
        """
        Main function to download from Snapchat link
        """
        print(f"🔍 Processing: {snapchat_link}")
        
        video_url = self.extract_video_url(snapchat_link)
        if video_url:
            return self.download_video(video_url, output_filename)
        return False
    
    def batch_download(self, links_file):
        """
        Download multiple videos from a file containing links
        """
        if not os.path.exists(links_file):
            print(f"❌ File not found: {links_file}")
            return
        
        success_count = 0
        failed_count = 0
        
        with open(links_file, 'r') as f:
            links = f.read().strip().split('\n')
        
        for i, link in enumerate(links, 1):
            link = link.strip()
            if link:
                print(f"\n[{i}/{len(links)}] Processing...")
                if self.download_from_link(link):
                    success_count += 1
                else:
                    failed_count += 1
        
        print(f"\n📊 Summary: {success_count} successful, {failed_count} failed")

def main():
    parser = argparse.ArgumentParser(
        description='Snapchat Video Downloader - Download videos without watermarks'
    )
    parser.add_argument(
        'url',
        nargs='?',
        help='Snapchat video URL'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output filename',
        default=None
    )
    parser.add_argument(
        '-b', '--batch',
        help='Batch download from file containing links',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    downloader = SnapchatVideoDownloader()
    
    if args.batch:
        if not args.url:
            print("❌ Please provide filename with -b option")
            sys.exit(1)
        downloader.batch_download(args.url)
    else:
        if not args.url:
            print("❌ Please provide a Snapchat video URL")
            print("\nUsage:")
            print("  python snapchat_video_downloader.py 'https://snap.tv/...'")
            print("  python snapchat_video_downloader.py -o 'filename.mp4' 'https://snap.tv/...'")
            print("  python snapchat_video_downloader.py -b links.txt")
            sys.exit(1)
        downloader.download_from_link(args.url, args.output)

if __name__ == "__main__":
    main()
