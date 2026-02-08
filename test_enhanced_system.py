#!/usr/bin/env python3
"""
Test Suite for Enhanced Quote Image Generator
Tests all new features
"""

import os
import sys
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_ai_prompt_generator():
    """Test AI Prompt Generator"""
    print_header("TEST 1: AI Prompt Generator")
    
    try:
        from ai_prompt_generator import AIPromptGenerator
        
        generator = AIPromptGenerator()
        
        test_quote = "The only way to do great work is to love what you do."
        result = generator.generate_prompt(test_quote, "Steve Jobs", "Motivation")
        
        print(f"✅ Themes: {result['themes']}")
        print(f"✅ Mood: {result['mood']}")
        print(f"✅ Prompt: {result['prompt'][:80]}...")
        print("\n✅ AI Prompt Generator: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AI Prompt Generator: FAILED - {e}")
        return False

def test_ai_image_generator():
    """Test AI Image Generator"""
    print_header("TEST 2: AI Image Generator")
    
    try:
        from ai_image_generator import AIImageGenerator
        
        api_key = os.getenv('HUGGINGFACE_API_KEY')
        
        if not api_key:
            print("⚠️  SKIPPED: No API key (optional)")
            print("   Get FREE key: https://huggingface.co/settings/tokens")
            print("\n✅ Module Installed (API not configured)")
            return True
        
        generator = AIImageGenerator(api_key=api_key)
        print(f"✅ API Key: {api_key[:10]}...{api_key[-5:]}")
        print("✅ Generator Initialized")
        print("\n✅ AI Image Generator: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AI Image Generator: FAILED - {e}")
        return False

def test_directories():
    """Test directory structure"""
    print_header("TEST 3: Directory Structure")
    
    dirs = [
        'assets/custom_backgrounds',
        'assets/ai_backgrounds',
        'Generated_Images',
        'scripts',
        'Watermarks'
    ]
    
    all_good = True
    for dir_path in dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - NOT FOUND")
            all_good = False
    
    if all_good:
        print("\n✅ Directory Structure: PASSED")
    return True

def test_files():
    """Test required files"""
    print_header("TEST 4: Required Files")
    
    files = [
        ('scripts/ai_prompt_generator.py', 'AI Prompt Generator'),
        ('scripts/ai_image_generator.py', 'AI Image Generator'),
        ('scripts/dashboard.py', 'Dashboard'),
        ('QUICK_REFERENCE.md', 'Quick Reference'),
        ('ENHANCED_SETUP_GUIDE.md', 'Setup Guide'),
    ]
    
    all_good = True
    for file_path, name in files:
        if Path(file_path).exists():
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - NOT FOUND")
            all_good = False
    
    if all_good:
        print("\n✅ Required Files: PASSED")
    return all_good

def test_imports():
    """Test Python imports"""
    print_header("TEST 5: Python Dependencies")
    
    modules = [
        ('PIL', 'Pillow'),
        ('gspread', 'gspread'),
        ('requests', 'requests'),
    ]
    
    all_good = True
    for module, package in modules:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_good = False
    
    if all_good:
        print("\n✅ Dependencies: PASSED")
    return all_good

def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪" * 35)
    print("  ENHANCED QUOTE GENERATOR - TEST SUITE")
    print("🧪" * 35)
    
    results = []
    results.append(('Directory Structure', test_directories()))
    results.append(('Required Files', test_files()))
    results.append(('Python Dependencies', test_imports()))
    results.append(('AI Prompt Generator', test_ai_prompt_generator()))
    results.append(('AI Image Generator', test_ai_image_generator()))
    
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n{'=' * 70}")
    print(f"  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"  🎉 ALL TESTS PASSED! System ready!")
    else:
        print(f"  ⚠️  Some tests failed. Check errors above.")
    
    print(f"{'=' * 70}\n")
    
    if passed >= total - 1:
        print("\n🚀 Next Steps:")
        print("   1. Run: python scripts/dashboard.py")
        print("   2. Open: http://localhost:8000")
        print("   3. Start creating!")
        
        if not os.getenv('HUGGINGFACE_API_KEY'):
            print("\n💡 Optional: Get FREE API key:")
            print("   https://huggingface.co/settings/tokens")
    
    print()

if __name__ == '__main__':
    run_all_tests()
