#!/usr/bin/env python3
"""
Diagnostic launcher for testing icon and QPainter issues.
"""

import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_icon():
    """Test icon loading separately."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        
        # Create minimal QApplication first
        app = QApplication([])
        
        icon_path = src_dir / "assets" / "icon.png"
        print(f"Icon path: {icon_path}")
        print(f"Icon exists: {icon_path.exists()}")
        
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            print(f"Icon loaded: {not icon.isNull()}")
            print(f"Available sizes: {icon.availableSizes()}")
        
        app.quit()
            
    except Exception as e:
        print(f"Error testing icon: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Launch diagnostic version."""
    print("=== Invoice Reconciliation Tool - Diagnostic Mode ===")
    
    # Test icon first
    test_icon()
    
    try:
        from src.gui.app import InvoiceReconciliationApp
        
        print("Starting GUI application...")
        app = InvoiceReconciliationApp()
        
        # Override to add more diagnostic info
        original_setup = app.setup_application
        
        def diagnostic_setup():
            qapp = original_setup()
            print(f"QApplication created successfully")
            print(f"Organization: {qapp.organizationName()}")
            print(f"Application name: {qapp.applicationName()}")
            
            icon = qapp.windowIcon()
            print(f"App icon set: {not icon.isNull()}")
            
            return qapp
        
        app.setup_application = diagnostic_setup
        
        result = app.run()
        print(f"Application exited with code: {result}")
        sys.exit(result)
        
    except ImportError as e:
        print(f"Error importing GUI components: {e}")
        print("Please ensure PySide6 is installed: uv pip install PySide6")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
