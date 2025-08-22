#!/usr/bin/env python3
"""
GUI Launcher for Invoice Reconciliator

This script launches the GUI version of the invoice reconciliation tool.
It provides a user-friendly interface for non-technical accountants.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Launch the GUI application."""
    try:
        # Import single instance manager
        from src.gui.single_instance import ensure_single_instance
        
        # Check for existing instance
        instance_manager, is_first_instance = ensure_single_instance("InvoiceReconciliator")
        
        if not is_first_instance:
            print("Another instance of Invoice Reconciliator is already running.")
            print("The existing window has been brought to the foreground.")
            sys.exit(0)
        
        # We're the first instance, proceed with launching
        from src.gui.app import InvoiceReconciliationApp
        
        app = InvoiceReconciliationApp(instance_manager)
        sys.exit(app.run())
        
    except ImportError as e:
        print(f"Error importing GUI components: {e}")
        print("Please ensure PySide6 is installed: uv pip install PySide6")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
