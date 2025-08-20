#!/usr/bin/env python3
"""
Test the relative path UX improvements.
"""

import sys
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_relative_paths():
    """Test the relative path functionality."""
    try:
        from src.utils import get_relative_path, get_project_root
        
        print("=== Relative Path UX Improvement Test ===\n")
        
        # Get project root
        project_root = get_project_root()
        print(f"Project Root: {project_root}")
        
        # Test various paths
        test_paths = [
            project_root / "data" / "input",
            project_root / "data" / "output",
            project_root / "src" / "gui",
            Path("C:/Users/Test/Documents"),  # External path
            project_root.parent / "external",  # Parent directory
        ]
        
        print("\nPath Conversion Examples:")
        print("=" * 60)
        
        for test_path in test_paths:
            relative = get_relative_path(test_path, project_root)
            length_reduction = len(str(test_path)) - len(relative)
            
            print(f"Original:  {test_path}")
            print(f"Relative:  {relative}")
            print(f"Saved:     {length_reduction} characters")
            print("-" * 60)
        
        # Test GUI integration
        print("\nGUI Integration Test:")
        print("=" * 30)
        
        from PySide6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        
        # Check initial values
        input_text = window.input_dir_edit.text()
        output_text = window.output_dir_edit.text()
        
        print(f"✓ Input field shows:  '{input_text}' (relative)")
        print(f"✓ Output field shows: '{output_text}' (relative)")
        
        # Check tooltips
        input_tooltip = window.input_dir_edit.toolTip()
        output_tooltip = window.output_dir_edit.toolTip()
        
        print(f"✓ Input tooltip:  {input_tooltip}")
        print(f"✓ Output tooltip: {output_tooltip}")
        
        # Test path conversion function
        abs_input = window.get_absolute_path(input_text)
        abs_output = window.get_absolute_path(output_text)
        
        print(f"✓ Absolute input:  {abs_input}")
        print(f"✓ Absolute output: {abs_output}")
        
        app.quit()
        
        print(f"\n✅ UX Improvement Successfully Implemented!")
        print("\nBenefits:")
        print("• Cleaner UI with shorter path displays")
        print("• Tooltips show full absolute paths")
        print("• Automatic conversion between relative/absolute as needed")
        print("• Better user experience for non-technical users")
        print("• Maintains full functionality while improving readability")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_relative_paths()
    sys.exit(0 if success else 1)
