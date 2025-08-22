#!/usr/bin/env python3
"""
Build script for creating Invoice Reconciliator executable

This script automates the process of building the executable using PyInstaller.
It handles cleanup, building, and provides helpful output.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Main build process."""
    print("🔨 Building Invoice Reconciliator Executable")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"   Removed {build_dir}")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"   Removed {dist_dir}")
    
    # Build with PyInstaller
    print("\n🏗️  Building executable with PyInstaller...")
    spec_file = project_root / "invoice_reconciliator.spec"
    
    try:
        # Run PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build completed successfully!")
            
            # Check if executable exists
            exe_path = dist_dir / "InvoiceReconciliator.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 Executable created: {exe_path}")
                print(f"📊 Size: {size_mb:.1f} MB")
                
                # Create a simple README for distribution
                readme_path = dist_dir / "README.txt"
                with open(readme_path, 'w') as f:
                    f.write("""Invoice Reconciliator - Executable Distribution

IMPORTANT: Configuration Required
================================

Before running the application, you MUST create a .env file in the same directory as this executable with your OpenRouter API configuration:

1. Create a file named ".env" (without quotes) in this folder
2. Add the following content (replace with your actual API key):

OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.0-flash-001

Optional settings you can add:
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SEC=30
ENABLE_STAMPING=true
STAMP_POSITION=bottom-right
STAMP_PIC_NAME=Default User

Running the Application:
========================
Simply double-click InvoiceReconciliator.exe to start the application.

The application will create data/input and data/output folders automatically.
Place your PDF files in the data/input directory and use the GUI to process them.

Troubleshooting:
================
- If the application doesn't start, check that your .env file is properly configured
- For debugging, you can run the executable from Command Prompt to see error messages
- Ensure you have sufficient disk space for processing large PDF files

Support:
========
For technical support, contact the development team.
""")
                
                print(f"📋 Created README: {readme_path}")
                
                print(f"\n🎉 Distribution ready in: {dist_dir}")
                print("\n📝 Next steps:")
                print("   1. Test the executable by running it")
                print("   2. Create a .env file with your OpenRouter API key")
                print("   3. Distribute the entire 'dist' folder to users")
                
            else:
                print("❌ Executable not found after build!")
                return False
        else:
            print(f"❌ Build failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
