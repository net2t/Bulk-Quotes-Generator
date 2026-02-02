#!/usr/bin/env python3
# Quick Fix - Install Enhanced Files
# No path strings in docstrings to avoid Unicode errors

import shutil
from pathlib import Path

print("=" * 60)
print("Quick Fix - Installing Enhanced Files")
print("=" * 60)

# Check where we are
current_dir = Path.cwd()
print(f"\nCurrent directory: {current_dir}")

# Check for scripts folder
scripts_dir = current_dir / "scripts"
if not scripts_dir.exists():
    print("\nError: 'scripts' folder not found!")
    print("Please run this from your project root folder")
    input("\nPress Enter to exit...")
    exit(1)

print(f"Found scripts folder: {scripts_dir}")

# Files to install
files_to_install = {
    'image_generator_enhanced.py': 'scripts/image_generator.py',
    'dashboard_enhanced.py': 'scripts/dashboard.py'
}

print("\nInstalling enhanced files...")

installed = []
for source_name, dest_path in files_to_install.items():
    source = current_dir / source_name
    dest = current_dir / dest_path
    
    if source.exists():
        # Backup existing file
        if dest.exists():
            backup = dest.with_suffix('.py.backup')
            shutil.copy2(dest, backup)
            print(f"  Backed up: {dest.name} -> {backup.name}")
        
        # Install new file
        shutil.copy2(source, dest)
        print(f"  Installed: {dest_path}")
        installed.append(dest_path)
    else:
        print(f"  Warning: {source_name} not found in current directory")

if len(installed) == 2:
    print("\n" + "=" * 60)
    print("SUCCESS! Enhanced files installed")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Run: python scripts\\dashboard.py")
    print("   2. Open browser: http://localhost:8000")
    print("\nYou'll see 16 design templates and new features!")
else:
    print("\nInstallation incomplete")
    print("Please ensure these files are in your project root:")
    print("  - image_generator_enhanced.py")
    print("  - dashboard_enhanced.py")

print("\nPress Enter to exit...")
input()
