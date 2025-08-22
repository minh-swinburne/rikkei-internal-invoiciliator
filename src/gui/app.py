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
    
    def __init__(self, instance_manager=None):
        """Initialize the application."""
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.logger = None
        self.instance_manager = instance_manager
        self.instance_listener = None
    
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
        
        # Set application icon (check multiple locations for bundled/dev versions)
        icon_paths = [
            # For bundled executable (PyInstaller)
            Path(sys._MEIPASS) / "assets" / "icon.ico" if hasattr(sys, '_MEIPASS') else None,
            Path(sys._MEIPASS) / "assets" / "icon.png" if hasattr(sys, '_MEIPASS') else None,
            # For development
            Path(__file__).parent.parent / "assets" / "icon.ico",
            Path(__file__).parent.parent / "assets" / "icon.png"
        ]
        
        icon_loaded = False
        for icon_path in icon_paths:
            if icon_path and icon_path.exists():
                try:
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        app.setWindowIcon(icon)
                        print(f"Application icon loaded from: {icon_path}")
                        icon_loaded = True
                        break
                except Exception as e:
                    print(f"Could not load icon from {icon_path}: {e}")
        
        if not icon_loaded:
            print("Warning: Could not load application icon from any location")
        
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
            
            # Set up single instance listener if we have an instance manager
            if self.instance_manager:
                from .single_instance import SingleInstanceListener
                
                def show_window():
                    """Callback to show main window when requested by another instance"""
                    if self.main_window:
                        self.main_window.show()
                        self.main_window.raise_()
                        self.main_window.activateWindow()
                
                self.instance_listener = SingleInstanceListener(
                    self.instance_manager, 
                    show_window_callback=show_window
                )
                self.instance_listener.start_listening()
            
            self.logger.info("GUI application started successfully")
            
            # Run the event loop
            result = self.app.exec()
            
            return result
            
        except Exception as e:
            print(f"Failed to start GUI application: {e}")
            if self.logger:
                self.logger.error(f"Failed to start GUI application: {e}", exc_info=True)
            return 1
        
        finally:
            # Clean up single instance resources
            if self.instance_listener:
                self.instance_listener.stop_listening()
            if self.instance_manager:
                self.instance_manager.cleanup()
                
            if self.logger:
                self.logger.info("=== Invoice Reconciliation GUI Closed ===")


def run_gui_app() -> int:
    """Entry point function to run the GUI application."""
    app = InvoiceReconciliationApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(run_gui_app())
