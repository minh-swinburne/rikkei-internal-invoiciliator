#!/usr/bin/env python3
"""
Debug launcher to test portable path resolution.
"""

import sys
import os
from pathlib import Path

def debug_paths():
    """Print debug information about paths and system state."""
    print("=== DEBUG PATH INFORMATION ===")
    print(f"sys.executable: {sys.executable}")
    print(f"__file__: {__file__}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Has _MEIPASS: {hasattr(sys, '_MEIPASS')}")
    
    if hasattr(sys, '_MEIPASS'):
        print(f"sys._MEIPASS: {sys._MEIPASS}")
    
    print("\n=== TESTING get_project_root() ===")
    try:
        # Add src to path
        current_dir = Path(__file__).parent
        src_dir = current_dir / "src"
        sys.path.insert(0, str(src_dir))
        
        from src.utils import get_project_root
        project_root = get_project_root()
        print(f"Project root: {project_root}")
        print(f"Project root exists: {project_root.exists()}")
        print(f"Project root is directory: {project_root.is_dir()}")
        
        # Test some expected paths
        test_paths = [
            project_root / "logs",
            project_root / "data",
            project_root / "data" / "input",
            project_root / "data" / "output"
        ]
        
        print("\n=== TESTING EXPECTED PATHS ===")
        for path in test_paths:
            print(f"{path}: exists={path.exists()}, is_dir={path.is_dir() if path.exists() else 'N/A'}")
            
    except Exception as e:
        print(f"Error testing get_project_root(): {e}")
        import traceback
        traceback.print_exc()

    print("\n=== TESTING SETTINGS IMPORT ===")
    try:
        from src.settings import settings
        print(f"Settings loaded successfully!")
        print(f"Input dir: {settings.input_dir}")
        print(f"Output dir: {settings.output_dir}")
    except Exception as e:
        print(f"Error loading settings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_paths()
    input("Press Enter to exit...")
