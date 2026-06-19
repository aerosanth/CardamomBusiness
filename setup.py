#!/usr/bin/env python
"""
Setup script for Cardamom Business Dashboard
Initializes the project and performs initial data scrape
"""

import sys
import os
import subprocess

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")

def print_step(step_num, text):
    """Print step number"""
    print(f"\n[Step {step_num}] {text}")

def run_command(cmd, description):
    """Run a shell command"""
    print(f"\n  → {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        if result.returncode == 0:
            print(f"  ✓ {description} completed")
            return True
        else:
            print(f"  ✗ {description} failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"\n✗ ERROR: Python 3.8+ required. You have Python {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def main():
    print_header("CARDAMOM BUSINESS - PROJECT SETUP")
    
    # Check Python version
    print_step(1, "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Check for virtual environment
    print_step(2, "Checking virtual environment")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment is active")
    else:
        print("⚠ WARNING: Virtual environment is NOT active")
        print("  It's recommended to create a virtual environment:")
        print("    Windows: python -m venv venv && venv\\Scripts\\activate")
        print("    macOS/Linux: python3 -m venv venv && source venv/bin/activate")
        response = input("\n  Continue anyway? (yes/no): ").lower()
        if response != 'yes':
            print("Setup cancelled")
            sys.exit(0)
    
    # Install dependencies
    print_step(3, "Installing dependencies")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing packages"):
        print("\n✗ Failed to install dependencies")
        sys.exit(1)
    
    # Perform initial scrape
    print_step(4, "Performing initial data scrape")
    print("\n  This may take 5-10 minutes on first run...")
    print("  (Scraping all historical data from website)\n")
    
    try:
        from scraper import main_scrape_initial
        if main_scrape_initial():
            print("\n✓ Initial scrape completed successfully")
        else:
            print("\n✗ Initial scrape failed")
            print("  Try running again: python scraper.py")
    except ImportError as e:
        print(f"\n✗ Error importing scraper: {e}")
        sys.exit(1)
    
    # Final instructions
    print_header("SETUP COMPLETE! 🎉")
    
    print("""
Next steps:

1. Run the Streamlit app locally:
   → streamlit run app.py

2. Deploy to Streamlit Cloud:
   a. Push to GitHub:
      → git add .
      → git commit -m "Initial commit"
      → git push origin main
   
   b. Deploy:
      → Go to share.streamlit.io
      → Select: ansSanthoshM/CardamomBusiness
      → Choose branch: main and file: app.py
      → Click Deploy

3. Embed in Google Sites:
   → Add your Streamlit URL to Google Sites as an iframe

4. Set up automatic daily updates:
   → GitHub Actions workflow is already configured
   → Daily scraping will run automatically

Need help? Check README.md for detailed instructions.
    """)

if __name__ == "__main__":
    main()
