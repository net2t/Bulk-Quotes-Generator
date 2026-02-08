#!/usr/bin/env python3
"""
Batch Quote Image Generator for Bulk Quotes Image Generator
Generate multiple images at once via CLI
Updated with new filename format and Database worksheet support
"""

import argparse
import os
import sys
from pathlib import Path

# Add scripts directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from sheet_reader import SheetReader
from image_generator import QuoteImageGenerator
from google_drive_uploader import DriveUploader

def main():
    parser = argparse.ArgumentParser(description='Batch generate quote images')
    parser.add_argument('--topic', required=True, help='Topic to generate from')
    parser.add_argument('--style', default='elegant', help='Style template to use')
    parser.add_argument('--count', type=int, default=10, help='Number of images to generate')
    parser.add_argument('--upload', action='store_true', help='Upload to Google Drive')
    
    args = parser.parse_args()
    
    print(f"\n🎨 Bulk Quotes Image Generator - Batch Mode")
    print(f"Topic: {args.topic}")
    print(f"Style: {args.style}")
    print(f"Count: {args.count}")
    print("="*50 + "\n")
    
    # Initialize components
    sheet_reader = SheetReader()
    image_gen = QuoteImageGenerator()
    
    # Connect to sheets (uses fixed URL)
    if not sheet_reader.connect():
        print("❌ Failed to connect to Google Sheets")
        return
    
    # Get quotes
    quotes = sheet_reader.get_quotes(args.topic)
    if not quotes:
        print(f"❌ No quotes found for topic: {args.topic}")
        return
    
    # Limit to requested count
    quotes = quotes[:args.count]
    
    # Generate images
    generated_paths = []
    for i, quote_data in enumerate(quotes, 1):
        print(f"[{i}/{len(quotes)}] Generating: {quote_data['quote'][:50]}...")
        
        try:
            image_path = image_gen.generate(
                quote_data['quote'],
                quote_data['author'],
                args.style,
                category=quote_data.get('category', '')
            )
            generated_paths.append(image_path)
            print(f"  ✅ Saved to: {Path(image_path).name}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Upload to Drive if requested
    if args.upload and generated_paths:
        print(f"\n📤 Uploading {len(generated_paths)} images to Google Drive...")
        uploader = DriveUploader()
        if uploader.connect():
            for path in generated_paths:
                link = uploader.upload_image(path, args.topic)
                if link:
                    print(f"  ✅ Uploaded: {link}")
                else:
                    print(f"  ❌ Failed to upload: {Path(path).name}")
    
    print(f"\n✅ Batch generation complete!")
    print(f"Generated {len(generated_paths)} images in: Generated_Images/")
    print(f"📁 Filename format: <Category> - <Quote> - <Author> - <DD-MM-YYYY_HHMM>.png")

if __name__ == '__main__':
    main()