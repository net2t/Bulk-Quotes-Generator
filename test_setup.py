#!/usr/bin/env python3
"""
Test script to verify Bulk Quotes Image Generator setup
"""

import sys
from pathlib import Path

def test_setup():
    print("🧪 Testing Bulk Quotes Image Generator Setup")
    print("=" * 50)
    
    # Test imports
    print("\n📦 Testing imports...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
        
        from sheet_reader import SheetReader
        print("✅ SheetReader imported successfully")
        
        from image_generator import QuoteImageGenerator
        print("✅ QuoteImageGenerator imported successfully")
        
        from google_drive_uploader import DriveUploader
        print("✅ DriveUploader imported successfully")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test file structure
    print("\n📁 Testing file structure...")
    required_dirs = [
        'scripts',
        'assets/fonts',
        'assets/ai_backgrounds', 
        'assets/custom_backgrounds',
        'Watermarks',
        'Generated_Images',
        'references'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/ exists")
        else:
            print(f"❌ {dir_path}/ missing")
    
    # Test files
    required_files = [
        'credentials.json',
        'references/config.json',
        'requirements.txt',
        'README.md'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
    
    # Test fonts
    print("\n🔤 Testing fonts...")
    font_dir = Path('assets/fonts')
    if font_dir.exists():
        fonts = list(font_dir.glob('*.ttf'))
        print(f"✅ Found {len(fonts)} font files:")
        for font in fonts:
            print(f"   - {font.name}")
    else:
        print("❌ Fonts directory missing")
    
    # Test sheet connection
    print("\n🔗 Testing Google Sheets connection...")
    try:
        reader = SheetReader()
        if reader.connect():
            print("✅ Connected to Google Sheets successfully")
            
            topics = reader.get_topics()
            print(f"✅ Found {len(topics)} topics: {topics}")
            
            if topics:
                quotes = reader.get_quotes(topics[0])
                print(f"✅ Found {len(quotes)} quotes in '{topics[0]}'")
                
        else:
            print("❌ Failed to connect to Google Sheets")
            
    except Exception as e:
        print(f"❌ Sheet connection error: {e}")
    
    # Test image generation
    print("\n🎨 Testing image generation...")
    try:
        generator = QuoteImageGenerator()
        test_path = generator.generate(
            quote="Test quote for setup verification",
            author="Setup Test",
            style="minimal",
            category="Test"
        )
        print(f"✅ Test image generated: {Path(test_path).name}")
        
    except Exception as e:
        print(f"❌ Image generation error: {e}")
    
    print("\n🎉 Setup test completed!")
    print("📋 If all tests pass, your Bulk Quotes Image Generator is ready to use!")
    print("🚀 Run 'python scripts/dashboard.py' to start the web dashboard")

if __name__ == "__main__":
    test_setup()