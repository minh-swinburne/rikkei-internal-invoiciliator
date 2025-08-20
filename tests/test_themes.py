#!/usr/bin/env python3
"""
Theme testing script for the invoice reconciliation GUI.
"""

import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_themes():
    """Test theme switching functionality."""
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        app = QApplication([])
        
        print("=== Theme Testing ===")
        print(f"Qt Version: {app.applicationVersion()}")
        print(f"Initial style: {app.style().objectName()}")
        
        # Create main window to test theme functionality
        window = MainWindow()
        
        # Test available themes
        available_themes = window.get_available_themes()
        print(f"\nAvailable themes:")
        for name, style in available_themes.items():
            print(f"  • {name}: '{style}'")
        
        # Test theme switching
        print(f"\nTesting theme switches:")
        for theme_name in available_themes.keys():
            try:
                window.change_theme(theme_name)
                current_style = app.style().objectName()
                print(f"  ✓ {theme_name}: {current_style}")
            except Exception as e:
                print(f"  ✗ {theme_name}: Failed - {e}")
        
        # Show window briefly
        window.show()
        print(f"\nGUI window displayed with final theme: {app.style().objectName()}")
        print("Theme testing completed successfully!")
        
        # Don't start the event loop, just test functionality
        app.quit()
        
    except Exception as e:
        print(f"Error during theme testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_themes()
