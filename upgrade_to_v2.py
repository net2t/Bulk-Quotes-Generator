#!/usr/bin/env python3
"""
Upgrade Script - Quote Image Generator v2.0
Safely upgrades your existing installation to the enhanced version
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_backup():
    """Backup existing files"""
    print("\n📦 Creating backup...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backups_root = Path("backups")
    backups_root.mkdir(exist_ok=True)
    backup_dir = backups_root / f"backup_{timestamp}"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        'scripts/image_generator.py',
        'scripts/dashboard.py',
    ]
    
    for file_path in files_to_backup:
        if Path(file_path).exists():
            dest = backup_dir / Path(file_path).name
            shutil.copy2(file_path, dest)
            print(f"  ✅ Backed up {file_path}")
    
    print(f"  💾 Backup saved to: {backup_dir}/")
    return backup_dir

def upgrade_files():
    """Copy enhanced files to scripts directory"""
    print("\n🚀 Upgrading to v2.0...")
    
    # Ensure scripts directory exists
    Path('scripts').mkdir(exist_ok=True)
    
    upgrades = [
        ('image_generator_enhanced.py', 'scripts/image_generator.py'),
        ('dashboard_enhanced.py', 'scripts/dashboard.py'),
    ]
    
    for source, dest in upgrades:
        if Path(source).exists():
            shutil.copy2(source, dest)
            print(f"  ✅ Installed {dest}")
        else:
            print(f"  ⚠️  Warning: {source} not found")
            print(f"      Make sure this script is in the same folder as the enhanced files")
    
    # Also copy to project root as backup option
    if Path('image_generator_enhanced.py').exists():
        if not Path('scripts/dashboard.py').exists():
            print("\n  💡 Tip: Running from project root, use: python scripts/dashboard.py")
    
def verify_installation():
    """Verify the upgrade was successful"""
    print("\n🔍 Verifying installation...")
    
    required_files = [
        'scripts/image_generator.py',
        'scripts/dashboard.py',
        'scripts/sheet_reader.py',
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING!")
            all_good = False
    
    return all_good

def show_new_features():
    """Display new features"""
    print("\n" + "="*60)
    print("✨ NEW FEATURES IN v2.0")
    print("="*60)
    print("""
🎨 16 Design Templates
   • 6 Original styles (Minimal, Bright, Elegant, Bold, Modern, Neon)
   • 10 NEW styles (Sunset, Professional, Vintage, Nature, Ocean,
     Cosmic, Dark Minimal, Creative Split, Geometric, Artistic)

👤 Enhanced Author Images
   • Always rendered as perfect circles
   • Bordered with subtle shadow
   • Position control (4 corners)
   • Better visibility

💧 Smart Watermark Modes
   • Corner - Classic placement
   • Diagonal Stripe - Tiled pattern
   • Color Match - Adapts to image colors ⭐NEW
   • Subtle Center - Transparent centered

🚀 Improved Generation
   • Better text shadows
   • Enhanced gradients
   • Professional typography
   • Optimized layouts
""")

def main():
    print("="*60)
    print("Quote Image Generator - Upgrade to v2.0")
    print("="*60)
    
    # Check if we're in the right directory
    if not Path('scripts').exists() and not Path('Generated_Images').exists():
        print("\n⚠️  Warning: You may not be in your project directory")
        print("Please run this script from your Quote Image Generator folder")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    
    # Create backup
    backup_dir = create_backup()
    
    # Upgrade files
    upgrade_files()
    
    # Verify
    success = verify_installation()
    
    if success:
        print("\n" + "="*60)
        print("✅ UPGRADE SUCCESSFUL!")
        print("="*60)
        show_new_features()
        print("\n📖 Next Steps:")
        print("   1. Read README_ENHANCED.md for full documentation")
        print("   2. Run: python scripts/dashboard.py")
        print("   3. Open: http://localhost:8000")
        print(f"\n💾 Your backup is saved in: {backup_dir}/")
        print("\n🎨 Enjoy creating beautiful quote images with 16 templates!")
    else:
        print("\n❌ Upgrade encountered issues")
        print(f"Your original files are backed up in: {backup_dir}/")
        print("Please check the errors above")

if __name__ == '__main__':
    main()
