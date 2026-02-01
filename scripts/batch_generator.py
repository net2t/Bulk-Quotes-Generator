#!/usr/bin/env python3
"""
Batch Quote Image Generator
Generate multiple images at once via CLI
"""

import argparse
from pathlib import Path
from sheet_reader import SheetReader
from image_generator import QuoteImageGenerator
from google_drive_uploader import DriveUploader
import os

def main():
    parser = argparse.ArgumentParser(description='Batch generate quote images')
    parser.add_argument('--topic', required=True, help='Topic to generate from')
    parser.add_argument('--style', default='bright', choices=['minimal', 'bright', 'elegant', 'bold', 'modern'])
    parser.add_argument('--count', type=int, default=10, help='Number of images to generate')
    parser.add_argument('--upload', action='store_true', help='Upload to Google Drive')
    
    args = parser.parse_args()
    
    print(f"\n🎨 Batch Quote Image Generator")
    print(f"Topic: {args.topic}")
    print(f"Style: {args.style}")
    print(f"Count: {args.count}")
    print("="*50 + "\n")
    
    # Initialize components
    sheet_reader = SheetReader()
    image_gen = QuoteImageGenerator()
    
    # Connect to sheets
    sheet_url = os.getenv('GOODREADS_SHEET_URL')
    if not sheet_reader.connect(sheet_url):
        print("❌ Failed to connect to Google Sheets")
        return
    
    # Get quotes
    quotes = sheet_reader.get_quotes_by_topic(args.topic)
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
                args.style
            )
            generated_paths.append(image_path)
            print(f"  ✅ Saved to: {image_path}")
            
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
                    print(f"  ❌ Failed to upload: {path}")
    
    print(f"\n✅ Batch generation complete!")
    print(f"Generated {len(generated_paths)} images in: Generated_Images/")

if __name__ == '__main__':
    main()
