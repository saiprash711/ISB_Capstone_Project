"""
Deployment Readiness Checker for Streamlit Cloud
Verifies all files are properly configured for deployment
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_file_size(filepath, max_size_mb=100):
    """Check if file size is within limits"""
    if not os.path.exists(filepath):
        return True
    
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > max_size_mb:
        print(f"   ⚠️  WARNING: File is {size_mb:.1f}MB (GitHub limit: {max_size_mb}MB)")
        return False
    else:
        print(f"   ℹ️  File size: {size_mb:.2f}MB")
        return True

def check_requirements_format(filepath):
    """Check if requirements.txt has proper format"""
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for version specifications
    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
    has_versions = any('>=' in line or '==' in line for line in lines)
    
    if has_versions:
        print("   ✅ Requirements have version specifications")
        return True
    else:
        print("   ⚠️  WARNING: Requirements should have version specifications")
        return False

def main():
    print("=" * 70)
    print("🚀 STREAMLIT CLOUD DEPLOYMENT READINESS CHECKER")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    
    # Check critical files
    print("📋 Checking Critical Files:")
    print("-" * 70)
    
    checks = [
        ("dashboard.py", "Main application file"),
        ("requirements.txt", "Python dependencies"),
        (".streamlit/config.toml", "Streamlit configuration"),
    ]
    
    for filepath, desc in checks:
        if not check_file_exists(filepath, desc):
            all_checks_passed = False
    
    print()
    
    # Check data file
    print("📊 Checking Data Files:")
    print("-" * 70)
    
    has_csv = check_file_exists("Filtered.csv", "Data file (CSV)")
    has_xlsx = check_file_exists("Filtered.xlsx", "Data file (Excel)")
    
    if has_csv:
        check_file_size("Filtered.csv")
    elif has_xlsx:
        check_file_size("Filtered.xlsx")
    else:
        print("❌ No data file found! Need either Filtered.csv or Filtered.xlsx")
        all_checks_passed = False
    
    print()
    
    # Check requirements format
    print("🔍 Checking Requirements Format:")
    print("-" * 70)
    if not check_requirements_format("requirements.txt"):
        all_checks_passed = False
    
    print()
    
    # Check optional files
    print("📦 Checking Optional Files:")
    print("-" * 70)
    check_file_exists("packages.txt", "System packages (optional)")
    check_file_exists(".python-version", "Python version specification")
    check_file_exists("README.md", "Documentation")
    
    print()
    
    # Summary
    print("=" * 70)
    if all_checks_passed:
        print("✅ ALL CRITICAL CHECKS PASSED!")
        print()
        print("Your app is ready for Streamlit Cloud deployment!")
        print()
        print("Next steps:")
        print("1. Commit and push all changes to GitHub:")
        print("   git add .")
        print('   git commit -m "Ready for Streamlit Cloud deployment"')
        print("   git push origin main")
        print()
        print("2. Go to: https://share.streamlit.io/")
        print("3. Click 'New app' or 'Reboot app'")
        print("4. Wait 3-5 minutes for deployment")
        print()
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before deploying.")
        print("See STREAMLIT_DEPLOYMENT_GUIDE.md for detailed help.")
        print()
    print("=" * 70)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
