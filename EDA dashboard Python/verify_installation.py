"""
Verification script for the EDA Dashboard dependencies
Run this to check if all required libraries are installed
"""

import sys

def check_library(name, import_name=None):
    """Check if a library is installed"""
    if import_name is None:
        import_name = name
    
    try:
        __import__(import_name)
        print(f"✅ {name} - Installed")
        return True
    except ImportError:
        print(f"❌ {name} - NOT installed")
        return False

def main():
    print("=" * 60)
    print("EDA Dashboard - Dependency Verification")
    print("=" * 60)
    print()
    
    # Core libraries
    print("Core Libraries:")
    print("-" * 60)
    core_libs = [
        ("Streamlit", "streamlit"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("Plotly", "plotly"),
        ("OpenPyXL", "openpyxl"),
        ("FPDF", "fpdf"),
    ]
    
    core_results = []
    for name, import_name in core_libs:
        core_results.append(check_library(name, import_name))
    
    print()
    
    # Forecasting libraries
    print("Forecasting Libraries (NEW):")
    print("-" * 60)
    forecast_libs = [
        ("Statsmodels", "statsmodels"),
        ("Scikit-learn", "sklearn"),
    ]
    
    forecast_results = []
    for name, import_name in forecast_libs:
        forecast_results.append(check_library(name, import_name))
    
    print()
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    core_count = sum(core_results)
    forecast_count = sum(forecast_results)
    total_count = core_count + forecast_count
    total_libs = len(core_results) + len(forecast_results)
    
    print(f"Core Libraries: {core_count}/{len(core_results)} installed")
    print(f"Forecasting Libraries: {forecast_count}/{len(forecast_results)} installed")
    print(f"Total: {total_count}/{total_libs} installed")
    print()
    
    if total_count == total_libs:
        print("✅ All dependencies installed! Dashboard is ready to run.")
        print()
        print("Run the dashboard with:")
        print("  streamlit run dashboard.py")
        print("Or:")
        print("  run_dashboard.bat")
        return 0
    else:
        print("⚠️  Some dependencies are missing!")
        print()
        
        if core_count < len(core_results):
            print("Missing core libraries. Install with:")
            print("  pip install streamlit pandas numpy plotly openpyxl fpdf")
            print()
        
        if forecast_count < len(forecast_results):
            print("Missing forecasting libraries. Install with:")
            print("  pip install statsmodels scikit-learn")
            print()
        
        print("Or install all at once:")
        print("  pip install -r requirements.txt")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
