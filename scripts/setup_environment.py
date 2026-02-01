#!/usr/bin/env python3
"""
Environment Setup Script for Quote Image Generator
Validates and prepares the working environment
"""

import os
import sys
from pathlib import Path

def check_credentials():
    """Check if Google credentials exist"""
    cred_path = Path("credentials.json")
    if not cred_path.exists():
        print("❌ credentials.json not found!")
        print("📝 Please place your Google Service Account credentials in the current directory")
        return False
    print("✅ credentials.json found")
    return True

def create_directories():
    """Create required directories"""
    dirs = ["Watermarks", "Generated_Images"]
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_name}/ directory")
        else:
            print(f"✅ {dir_name}/ directory exists")

def check_packages():
    """Check and install required Python packages"""
    packages = {
        "PIL": "pillow",
        "gspread": "gspread",
        "google.oauth2": "google-auth",
        "googleapiclient": "google-api-python-client",
        "flask": "flask",
    }
    
    missing = []
    for module, package in packages.items():
        try:
            __import__(module.split('.')[0])
            print(f"✅ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} not installed")
    
    if missing:
        print(f"\n📦 Installing missing packages: {', '.join(missing)}")
        os.system(f"pip install {' '.join(missing)}")
        return True
    return True

def main():
    print("🚀 Quote Image Generator - Environment Setup\n")
    print("=" * 50)
    
    # Check credentials
    if not check_credentials():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Check packages
    print("\n📦 Checking Python packages...")
    check_packages()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete! You can now run:")
    print("   python scripts/dashboard.py")

if __name__ == "__main__":
    main()
