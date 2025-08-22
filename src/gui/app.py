"""
GUI application entry point for invoice reconciliation tool.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from .main_window import MainWindow
from ..logging_config import setup_logging, get_module_logger


class InvoiceReconciliationApp:
    """Main GUI application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.logger = None
    
    def setup_application(self) -> QApplication:
        """Set up the QApplication with proper settings."""
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Invoice Reconciliator")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("KDDI")
        app.setOrganizationDomain("kddi.com")
        
        # Enable high DPI scaling
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # Try to set a stable style to avoid rendering issues
        try:
            import platform
            if platform.system() == "Windows":
                # Use Windows Vista style which is more stable and looks nice
                app.setStyle("windowsvista")
                print("Set default style to Windows Vista")
        except Exception as e:
            # If style setting fails, continue with default
            print(f"Could not set default style: {e}")
        
        # Set application icon (if available)
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    # Scale down large icons to prevent rendering issues
                    app.setWindowIcon(icon)
            except Exception as e:
                # Silently ignore icon loading errors to prevent QPainter issues
                print(f"Warning: Could not load application icon: {e}")
        
        return app
    
    def setup_logging(self) -> None:
        """Set up logging for the GUI application."""
        self.logger = setup_logging(
            log_level="INFO",
            console_output=True,  # Enable console output for debugging
            is_test=False
        )
        self.logger.info("=== Invoice Reconciliation GUI Started ===")
    
    def run(self) -> int:
        """Run the GUI application."""
        try:
            # Set up logging first
            self.setup_logging()
            
            # Create and configure QApplication
            self.app = self.setup_application()
            
            # Create and show main window
            self.main_window = MainWindow()
            self.main_window.show()
            
            self.logger.info("GUI application started successfully")
            
            # Run the event loop
            return self.app.exec()
            
        except Exception as e:
            print(f"Failed to start GUI application: {e}")
            if self.logger:
                self.logger.error(f"Failed to start GUI application: {e}", exc_info=True)
            return 1
        
        finally:
            if self.logger:
                self.logger.info("=== Invoice Reconciliation GUI Closed ===")


def run_gui_app() -> int:
    """Entry point function to run the GUI application."""
    app = InvoiceReconciliationApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(run_gui_app())
