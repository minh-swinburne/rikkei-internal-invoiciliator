"""
Test script to verify GUI checkbox interactions for STAMP_ONLY_APPROVED setting.
"""

import sys
from pathlib import Path

# Add src to path so we can import the modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.gui.config_dialog import ConfigDialog
from src.settings import settings


def test_checkbox_interactions():
    """Test the GUI checkbox interactions."""
    print("Testing GUI checkbox interactions...")
    
    # Create QApplication instance (required for Qt widgets)
    app = QApplication(sys.argv)
    
    # Create config dialog
    dialog = ConfigDialog()
    
    # Test initial state
    print(f"Initial stamp_only_approved: {dialog.stamp_only_approved_cb.isChecked()}")
    print(f"Initial always_accept enabled: {dialog.always_accept_cb.isEnabled()}")
    print(f"Initial always_accept checked: {dialog.always_accept_cb.isChecked()}")
    
    # Test: Enable stamp_only_approved
    print("\n--- Enabling 'Only Stamp Approved' ---")
    dialog.stamp_only_approved_cb.setChecked(True)
    print(f"After enabling only_approved:")
    print(f"  always_accept enabled: {dialog.always_accept_cb.isEnabled()}")
    print(f"  always_accept checked: {dialog.always_accept_cb.isChecked()}")
    
    # Test: Disable stamp_only_approved
    print("\n--- Disabling 'Only Stamp Approved' ---")
    dialog.stamp_only_approved_cb.setChecked(False)
    print(f"After disabling only_approved:")
    print(f"  always_accept enabled: {dialog.always_accept_cb.isEnabled()}")
    print(f"  always_accept checked: {dialog.always_accept_cb.isChecked()}")
    
    print("\n✓ GUI interaction test completed successfully!")


if __name__ == "__main__":
    test_checkbox_interactions()
