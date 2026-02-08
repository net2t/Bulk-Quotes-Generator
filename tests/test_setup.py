#!/usr/bin/env python3
"""
Test script to verify Bulk Quotes Image Generator setup
"""

import sys
from pathlib import Path

def test_setup():
    print("🧪 Testing Bulk Quotes Image Generator Setup")
    print("=" * 50)

    root_dir = Path(__file__).resolve().parent.parent
    
    # Test imports
    print("\n📦 Testing imports...")
    try:
        sys.path.insert(0, str(root_dir / 'scripts'))
        
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
        root_dir / 'scripts',
        root_dir / 'assets' / 'fonts',
        root_dir / 'assets' / 'ai_backgrounds',
        root_dir / 'assets' / 'custom_backgrounds',
        root_dir / 'Watermarks',
        root_dir / 'Generated_Images',
        root_dir / 'references'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            rel = Path(dir_path).relative_to(root_dir)
            print(f"✅ {rel}/ exists")
        else:
            rel = Path(dir_path)
            try:
                rel = rel.relative_to(root_dir)
            except Exception:
                pass
            print(f"❌ {rel}/ missing")
    
    # Test files
    required_files = [
        root_dir / 'credentials.json',
        root_dir / 'references' / 'config.json',
        root_dir / 'requirements.txt',
        root_dir / 'README.md'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            rel = Path(file_path).relative_to(root_dir)
            print(f"✅ {rel} exists")
        else:
            rel = Path(file_path)
            try:
                rel = rel.relative_to(root_dir)
            except Exception:
                pass
            print(f"❌ {rel} missing")
    
    # Test fonts
    print("\n🔤 Testing fonts...")
    font_dir = root_dir / 'assets' / 'fonts'
    
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