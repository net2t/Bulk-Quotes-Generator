#!/usr/bin/env python3
"""
Quick Fix - Moves enhanced files to correct location
Run this from your project root: C:\Users\NADEEM\Downloads\Quotes Images\
"""

import shutil
from pathlib import Path

print("🔧 Quick Fix - Installing Enhanced Files")
print("=" * 60)

# Check where we are
current_dir = Path.cwd()
print(f"\nCurrent directory: {current_dir}")

# Check for scripts folder
scripts_dir = current_dir / "scripts"
if not scripts_dir.exists():
    print("\n❌ Error: 'scripts' folder not found!")
    print("Please run this from your project root folder")
    print("Expected location: C:\\Users\\NADEEM\\Downloads\\Quotes Images\\")
    input("\nPress Enter to exit...")
    exit(1)

print(f"✅ Found scripts folder: {scripts_dir}")

# Files to install
files_to_install = {
    'image_generator_enhanced.py': 'scripts/image_generator.py',
    'dashboard_enhanced.py': 'scripts/dashboard.py'
}

print("\n📦 Installing enhanced files...")

installed = []
for source_name, dest_path in files_to_install.items():
    source = current_dir / source_name
    dest = current_dir / dest_path
    
    if source.exists():
        # Backup existing file
        if dest.exists():
            backup = dest.with_suffix('.py.backup')
            shutil.copy2(dest, backup)
            print(f"  💾 Backed up: {dest.name} → {backup.name}")
        
        # Install new file
        shutil.copy2(source, dest)
        print(f"  ✅ Installed: {dest_path}")
        installed.append(dest_path)
    else:
        print(f"  ⚠️  Not found: {source_name}")
        print(f"      Please ensure {source_name} is in: {current_dir}")

if len(installed) == 2:
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Enhanced files installed")
    print("=" * 60)
    print("\n🚀 Next steps:")
    print("   1. Open a NEW terminal/PowerShell window")
    print("   2. Navigate to: C:\\Users\\NADEEM\\Downloads\\Quotes Images")
    print("   3. Run: python scripts\\dashboard.py")
    print("   4. Open browser: http://localhost:8000")
    print("\n✨ You'll see 16 design templates and new features!")
else:
    print("\n❌ Installation incomplete")
    print("Please ensure these files are in your project root:")
    print("  - image_generator_enhanced.py")
    print("  - dashboard_enhanced.py")

input("\nPress Enter to exit...")
