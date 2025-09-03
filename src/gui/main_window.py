"""
Main window for the invoice reconciliation GUI application.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QPushButton, QLineEdit, QLabel, QProgressBar,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu, QSplitter,
    QApplication, QStyleFactory
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSettings
from PySide6.QtGui import QAction, QFont, QIcon, QActionGroup, QColor, QPalette

from .config_dialog import ConfigDialog
from .log_viewer import LogViewer
from .result_viewer import ResultDetailViewer
from .help_dialog import HelpDialog
from .qt_logging import QtLogHandler, LogCapture
from ..core import InvoiceReconciliationEngine
from ..core.thread import ProcessingThread, RetryThread
from ..settings import settings
from ..logging_config import get_module_logger
from ..utils import get_relative_path, get_project_root, load_json, normalize_path_display, get_application_version


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_module_logger('gui.main_window')
        
        # Project root for relative path calculations
        self.project_root = get_project_root()
        
        # Set up permanent log capture for GUI
        self.log_handler = QtLogHandler()
        self.log_handler.log_message.connect(self.on_log_message)
        self._setup_permanent_log_capture()
        
        # Core components
        self.engine: Optional[InvoiceReconciliationEngine] = None
        self.processing_thread: Optional[ProcessingThread] = None
        self.retry_thread: Optional[RetryThread] = None
        self.output_dir: Optional[Path] = None
        self.is_processing_paused: bool = False
        
        # UI components
        self.input_dir_edit: Optional[QLineEdit] = None
        self.output_dir_edit: Optional[QLineEdit] = None
        self.pic_name_edit: Optional[QLineEdit] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.status_label: Optional[QLabel] = None
        self.current_file_label: Optional[QLabel] = None
        self.start_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.pause_processing_btn: Optional[QPushButton] = None
        self.log_viewer: Optional[LogViewer] = None
        self.result_table: Optional[QTableWidget] = None
        
        # Result storage for accessing paths later
        self.result_data: dict = {}  # filename -> result_dict mapping
        
        # Theme management
        self.theme_actions: dict = {}
        self.theme_group: Optional[QActionGroup] = None
        self.settings = QSettings()
        
        self.setup_ui()
        self.setup_menu()
        self.load_settings()
        self.load_theme()
        self.update_ui_state()
        
        # Add timer for initial theme refresh
        QTimer.singleShot(200, self._refresh_all_themes)
    
    def _detect_dark_mode(self) -> bool:
        """Detect if we're in dark mode."""
        try:
            app: QApplication = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                # If window background is darker than 128, assume dark mode
                return window_color.lightness() < 128
        except Exception:
            pass
        return False
    
    def _setup_permanent_log_capture(self):
        """Set up permanent log capture to show all application logs in the GUI."""
        import logging
        
        # Only add handler to the root logger to avoid duplicates from propagation
        root_logger = logging.getLogger('invoice_reconciliator')
        
        # Only add if not already present
        if self.log_handler not in root_logger.handlers:
            root_logger.addHandler(self.log_handler)
            # Set level to capture all messages
            if root_logger.level == logging.NOTSET or root_logger.level > logging.DEBUG:
                root_logger.setLevel(logging.DEBUG)
        
        # Ensure all child loggers propagate to the root logger (this is default behavior)
        # but just to be explicit about it:
        child_logger_names = [
            'invoice_reconciliator.gui',
            'invoice_reconciliator.core', 
            'invoice_reconciliator.engine',
            'invoice_reconciliator.pdf_processor',
            'invoice_reconciliator.llm_extractor',
            'invoice_reconciliator.validator',
            'invoice_reconciliator.file_manager',
            'invoice_reconciliator.service_manager'
        ]
        
        for logger_name in child_logger_names:
            logger = logging.getLogger(logger_name)
            # Ensure propagation is enabled (default is True)
            logger.propagate = True
            # Set appropriate level for child loggers
            if logger.level == logging.NOTSET or logger.level > logging.DEBUG:
                logger.setLevel(logging.DEBUG)
    
    def closeEvent(self, event):
        """Handle application close event to clean up log handlers."""
        import logging
        
        # Remove our handler from the root logger only
        root_logger = logging.getLogger('invoice_reconciliator')
        if self.log_handler in root_logger.handlers:
            root_logger.removeHandler(self.log_handler)
        
        # Call parent close event
        super().closeEvent(event)
    
    def _refresh_all_themes(self):
        """Refresh themes for all components."""
        try:
            if hasattr(self, 'log_viewer') and self.log_viewer:
                self.log_viewer.refresh_theme()
            # Refresh result table if it has items
            if hasattr(self, 'result_table') and self.result_table.rowCount() > 0:
                self._refresh_result_table_colors()
        except Exception as e:
            self.logger.error(f"Error refreshing themes: {e}")
    
    def _refresh_result_table_colors(self):
        """Refresh colors for all items in the result table."""
        try:
            is_dark = self._detect_dark_mode()
            for row in range(self.result_table.rowCount()):
                status_item = self.result_table.item(row, 1)  # Status column
                if status_item:
                    status = status_item.text()
                    self._apply_status_colors(status_item, status, is_dark)
                    
                issues_item = self.result_table.item(row, 2)  # Issues column
                if issues_item:
                    issues_count = int(issues_item.text()) if issues_item.text().isdigit() else 0
                    self._apply_issues_colors(issues_item, issues_count, is_dark)
        except Exception as e:
            self.logger.error(f"Error refreshing result table colors: {e}")
    
    def _apply_status_colors(self, item: QTableWidgetItem, status: str, is_dark: bool):
        """Apply theme-appropriate colors to status items."""
        if status == 'APPROVED':
            if is_dark:
                item.setBackground(QColor(129, 199, 132, 100))  # Light green with higher opacity for dark mode
                item.setForeground(QColor(200, 230, 201))  # Very light green text
            else:
                item.setBackground(QColor(76, 175, 80, 77))  # Nice green with 30% opacity
                item.setForeground(QColor(27, 94, 32))  # Dark green text
        elif status in ['REQUIRES REVIEW', 'REQUIRES_REVIEW']:
            if is_dark:
                item.setBackground(QColor(255, 224, 130, 100))  # Light amber with higher opacity for dark mode
                item.setForeground(QColor(255, 245, 157))  # Very light amber text
            else:
                item.setBackground(QColor(255, 193, 7, 77))  # Nice amber with 30% opacity  
                item.setForeground(QColor(255, 111, 0))  # Dark orange text
        elif status in ['FAILED', 'failed']:
            if is_dark:
                item.setBackground(QColor(239, 154, 154, 100))  # Light red with higher opacity for dark mode
                item.setForeground(QColor(255, 205, 210))  # Very light red text
            else:
                item.setBackground(QColor(244, 67, 54, 77))  # Nice red with 30% opacity
                item.setForeground(QColor(183, 28, 28))  # Dark red text
        else:
            if is_dark:
                item.setBackground(QColor(189, 189, 189, 100))  # Light gray with higher opacity for dark mode
                item.setForeground(QColor(224, 224, 224))  # Very light gray text
            else:
                item.setBackground(QColor(158, 158, 158, 51))  # Light gray with 20% opacity
                item.setForeground(QColor(97, 97, 97))  # Dark gray text
    
    def _apply_issues_colors(self, item: QTableWidgetItem, issues_count: int, is_dark: bool):
        """Apply theme-appropriate colors to issues items."""
        if issues_count > 0:
            if is_dark:
                item.setBackground(QColor(255, 224, 130, 100))  # Light amber with higher opacity for dark mode
                item.setForeground(QColor(255, 245, 157))  # Very light amber text
            else:
                item.setBackground(QColor(255, 193, 7, 77))  # Nice amber with 30% opacity
                item.setForeground(QColor(255, 111, 0))  # Dark orange text
        else:
            if is_dark:
                item.setBackground(QColor(129, 199, 132, 100))  # Light green with higher opacity for dark mode
                item.setForeground(QColor(200, 230, 201))  # Very light green text
            else:
                item.setBackground(QColor(76, 175, 80, 77))  # Nice green with 30% opacity
                item.setForeground(QColor(27, 94, 32))  # Dark green text
    
    def _resize_table_to_fit_content(self):
        """Resize table to better fit its content while maintaining user column sizes."""
        try:
            if not self.result_table or self.result_table.rowCount() == 0:
                return
            
            # Resize rows to content
            self.result_table.resizeRowsToContents()
            
            # Optionally adjust the table height to show all rows (with a reasonable max)
            row_count = self.result_table.rowCount()
            if row_count > 0:
                # Calculate total height needed
                header_height = self.result_table.horizontalHeader().height()
                row_height = self.result_table.rowHeight(0)  # Assume all rows same height
                total_height = header_height + (row_height * min(row_count, 10))  # Max 10 rows visible
                
                # Set a reasonable maximum height to avoid taking too much space
                max_height = 400
                preferred_height = min(total_height + 20, max_height)  # +20 for margins
                
                # Don't set if current height is reasonable
                current_height = self.result_table.height()
                if abs(current_height - preferred_height) > 50:  # Only resize if significant difference
                    self.result_table.setMinimumHeight(min(150, preferred_height))
                    self.result_table.setMaximumHeight(max_height)
            
            self.logger.debug(f"Resized table to fit {row_count} rows")
            
        except Exception as e:
            self.logger.error(f"Error resizing table: {e}")
    
    def _show_table_context_menu(self, position):
        """Show context menu for the result table."""
        try:
            from PySide6.QtWidgets import QMenu
            
            menu = QMenu(self)
            
            # Resize to fit content action
            resize_action = menu.addAction("Resize Columns to Fit Content")
            resize_action.triggered.connect(self._resize_columns_to_content)
            
            # Reset column widths action
            reset_action = menu.addAction("Reset Column Widths")
            reset_action.triggered.connect(self._reset_column_widths)
            
            menu.addSeparator()
            
            # Copy action (if there's a selection)
            if self.result_table.selectedItems():
                copy_action = menu.addAction("Copy Selected")
                copy_action.triggered.connect(self._copy_selected_cells)
            
            # Show menu at cursor position
            menu.exec(self.result_table.mapToGlobal(position))
            
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _resize_columns_to_content(self):
        """Resize columns to fit their content."""
        try:
            self.result_table.resizeColumnsToContents()
            self.logger.debug("Resized columns to fit content")
        except Exception as e:
            self.logger.error(f"Error resizing columns: {e}")
    
    def _reset_column_widths(self):
        """Reset column widths to default values."""
        try:
            self.result_table.setColumnWidth(0, 360)  # File Name
            self.result_table.setColumnWidth(1, 120)  # Status
            self.result_table.setColumnWidth(2, 100)   # Issues
            self.result_table.setColumnWidth(3, 200)  # Actions
            self.logger.debug("Reset column widths to defaults")
        except Exception as e:
            self.logger.error(f"Error resetting column widths: {e}")
    
    def _copy_selected_cells(self):
        """Copy selected cells to clipboard."""
        try:
            from PySide6.QtGui import QGuiApplication
            
            selected_items = self.result_table.selectedItems()
            if not selected_items:
                return
            
            # Get the text of all selected items
            text_data = []
            for item in selected_items:
                if item.text():
                    text_data.append(item.text())
            
            if text_data:
                clipboard_text = "\t".join(text_data)
                QGuiApplication.clipboard().setText(clipboard_text)
                self.logger.debug(f"Copied {len(text_data)} cells to clipboard")
            
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
    
    def set_application_icon(self):
        """Set the application icon with PyInstaller compatibility."""
        try:
            # Try multiple icon file paths for different deployment scenarios
            possible_icon_paths = [
                # Development environment
                Path(__file__).parent.parent / "assets" / "icon.ico",
                Path(__file__).parent.parent / "assets" / "icon.png",
                # PyInstaller bundle (relative to executable)
                Path(sys.executable).parent / "assets" / "icon.ico",
                Path(sys.executable).parent / "assets" / "icon.png",
                Path(sys.executable).parent / "icon.ico",
                Path(sys.executable).parent / "icon.png",
                # Project root directory
                self.project_root / "assets" / "icon.ico",
                self.project_root / "assets" / "icon.png",
                self.project_root / "icon.ico",
                self.project_root / "icon.png"
            ]
            
            # Try each path until we find an icon
            for icon_path in possible_icon_paths:
                if icon_path.exists():
                    try:
                        icon = QIcon(str(icon_path))
                        if not icon.isNull():
                            self.setWindowIcon(icon)
                            # Also set application icon for all windows
                            app: QApplication = QApplication.instance()
                            if app:
                                app.setWindowIcon(icon)
                            self.logger.debug(f"Successfully loaded icon from: {icon_path}")
                            return
                    except Exception as e:
                        self.logger.debug(f"Failed to load icon from {icon_path}: {e}")
                        continue
            
            self.logger.warning("No application icon found in any of the expected locations")
            
        except Exception as e:
            self.logger.error(f"Error setting application icon: {e}")
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Invoice Reconciliator")
        self.setMinimumSize(800, 600)
        self.resize(800, 700)
        
        # Set window icon with PyInstaller compatibility
        self.set_application_icon()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Top section with configuration and status
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(top_splitter)
        
        # Configuration group
        config_group = self.create_configuration_group()
        top_splitter.addWidget(config_group)
        
        # Status group  
        status_group = self.create_status_group()
        top_splitter.addWidget(status_group)
        
        # Set splitter proportions
        top_splitter.setSizes([400, 400])
        
        # Bottom section with logs and results
        bottom_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(bottom_splitter)
        
        # Log viewer
        self.log_viewer = LogViewer()
        bottom_splitter.addWidget(self.log_viewer)
        
        # Results table
        results_group = self.create_results_group()
        bottom_splitter.addWidget(results_group)
        
        # Set bottom splitter proportions
        bottom_splitter.setSizes([300, 250])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_configuration_group(self) -> QGroupBox:
        """Create the configuration group box."""
        group = QGroupBox("Configuration")
        layout = QGridLayout(group)
        
        # Input directory
        layout.addWidget(QLabel("Input Directory:"), 0, 0)
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText("Select folder containing PDF files...")
        self.input_dir_edit.setToolTip("Folder containing merged PDF files (invoice + purchase order)")
        layout.addWidget(self.input_dir_edit, 0, 1)
        
        input_browse_btn = QPushButton("Browse")
        input_browse_btn.setToolTip("Select folder containing PDF files to process")
        input_browse_btn.clicked.connect(self.browse_input_directory)
        layout.addWidget(input_browse_btn, 0, 2)
        
        # Output directory
        layout.addWidget(QLabel("Output Directory:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output folder...")
        self.output_dir_edit.setToolTip("Folder where processed files and reports will be saved")
        layout.addWidget(self.output_dir_edit, 1, 1)
        
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.setToolTip("Select folder where processed files will be saved")
        output_browse_btn.clicked.connect(self.browse_output_directory)
        layout.addWidget(output_browse_btn, 1, 2)
        
        # PIC Name
        layout.addWidget(QLabel("PIC Name:"), 2, 0)
        self.pic_name_edit = QLineEdit()
        self.pic_name_edit.setText(settings.stamp_pic_name)
        self.pic_name_edit.setToolTip("Person in charge name for PDF stamping")
        layout.addWidget(self.pic_name_edit, 2, 1, 1, 2)
        
        # Settings button
        settings_btn = QPushButton("Advanced Settings...")
        settings_btn.setToolTip("Configure API keys, processing options, and advanced settings")
        settings_btn.clicked.connect(self.show_settings_dialog)
        layout.addWidget(settings_btn, 3, 0, 1, 3)
        
        return group
    
    def create_status_group(self) -> QGroupBox:
        """Create the processing status group box."""
        group = QGroupBox("Processing Status")
        layout = QGridLayout(group)
        
        # Status
        layout.addWidget(QLabel("Status:"), 0, 0)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        layout.addWidget(self.status_label, 0, 1)
        
        # Progress bar
        layout.addWidget(QLabel("Progress:"), 1, 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar, 1, 1)
        
        # Current file
        layout.addWidget(QLabel("Current File:"), 2, 0)
        self.current_file_label = QLabel("None")
        layout.addWidget(self.current_file_label, 2, 1)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Processing")
        self.start_button.setToolTip("Begin processing all PDF files in the input directory")
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Stop processing and cancel remaining files")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Pause/Resume button for processing workflow
        self.pause_processing_btn = QPushButton("Pause Processing")
        self.pause_processing_btn.setToolTip("Pause processing - files in progress will complete")
        self.pause_processing_btn.clicked.connect(self.toggle_processing_pause)
        self.pause_processing_btn.setEnabled(False)  # Only enabled during processing
        button_layout.addWidget(self.pause_processing_btn)
        
        # Help button
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(30)
        help_btn.setToolTip("Show User Guide (F1)")
        help_btn.clicked.connect(self.show_user_guide)
        button_layout.addWidget(help_btn)
        
        layout.addLayout(button_layout, 3, 0, 1, 2)
        
        return group
    
    def create_results_group(self) -> QGroupBox:
        """Create the results group box."""
        group = QGroupBox("Processing Results")
        layout = QVBoxLayout(group)
        
        # Results table
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["File Name", "Status", "Issues", "Actions"])
        
        # Set column widths - all interactive but with different default sizes
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Set minimum and default column widths
        header.setMinimumSectionSize(80)
        header.setStretchLastSection(True)
        self.result_table.setColumnWidth(0, 360)  # File Name - wider default
        self.result_table.setColumnWidth(1, 120)  # Status
        self.result_table.setColumnWidth(2, 100)   # Issues
        # self.result_table.setColumnWidth(3, 200)  # Actions
        
        # Enable sorting
        self.result_table.setSortingEnabled(True)
        
        # Set up context menu for the table
        self.result_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self._show_table_context_menu)
        
        # Enable double-click to view details
        self.result_table.doubleClicked.connect(self.on_result_double_clicked)

        layout.addWidget(self.result_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Results")
        refresh_btn.setToolTip("Reload processing results from the output directory")
        refresh_btn.clicked.connect(self.refresh_results)
        button_layout.addWidget(refresh_btn)
        
        import_button = QPushButton("Import Results")
        import_button.clicked.connect(self.import_results)
        import_button.setToolTip("Import existing JSON result files from a folder")
        button_layout.addWidget(import_button)
        
        export_btn = QPushButton("Export Results")
        export_btn.setToolTip("Export processing results to Excel or CSV file")
        export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(export_btn)
        
        open_output_btn = QPushButton("Open Output Folder")
        open_output_btn.setToolTip("Open the output folder in file explorer")
        open_output_btn.clicked.connect(self.open_output_folder)
        button_layout.addWidget(open_output_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return group
    
    def setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        config_action = QAction("Configuration...", self)
        config_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(config_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        self.setup_theme_menu(theme_menu)
        
        view_menu.addSeparator()
        
        # Reset layout action
        reset_layout_action = QAction("Reset Window Layout", self)
        reset_layout_action.triggered.connect(self.reset_window_layout)
        view_menu.addAction(reset_layout_action)
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # User Guide action
        user_guide_action = QAction("User Guide...", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
        
        about_action = QAction("About...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        # Debug: Show available styles
        styles_action = QAction("Available Styles (Debug)", self)
        styles_action.triggered.connect(self.show_available_styles)
        help_menu.addAction(styles_action)
    
    def load_settings(self):
        """Load settings into the UI."""
        # Load directories from QSettings, with settings defaults as fallback
        input_dir = self.settings.value("input_dir", settings.input_dir)
        output_dir = self.settings.value("output_dir", settings.output_dir)
        pic_name = self.settings.value("pic_name", settings.stamp_pic_name)
        
        self.input_dir_edit.setText(input_dir)
        self.output_dir_edit.setText(output_dir)
        self.pic_name_edit.setText(pic_name)
        
        # Set tooltips to show full paths
        input_full_path = self.get_absolute_path(input_dir)
        output_full_path = self.get_absolute_path(output_dir)
        self.input_dir_edit.setToolTip(f"Full path: {input_full_path}")
        self.output_dir_edit.setToolTip(f"Full path: {output_full_path}")
        
        # Also update global settings with current values
        settings.input_dir = input_dir
        settings.output_dir = output_dir
        
        # Load network settings from QSettings as backup (main source is .env file via settings object)
        self._load_network_settings_from_qsettings()
    
    def reload_config_settings(self):
        """Reload only the settings that might have changed from config dialog."""
        # Only update PIC name from global settings, preserve directories
        self.pic_name_edit.setText(settings.stamp_pic_name)
        
        # Save updated network settings to QSettings as backup
        self._save_network_settings_to_qsettings()
        self.settings.sync()
    
    def save_settings(self):
        """Save current UI settings."""
        try:
            # Save window geometry
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            
            # Save directory paths to both QSettings and global settings
            input_dir = self.input_dir_edit.text()
            output_dir = self.output_dir_edit.text()
            pic_name = self.pic_name_edit.text()
            
            self.settings.setValue("input_dir", input_dir)
            self.settings.setValue("output_dir", output_dir)
            self.settings.setValue("pic_name", pic_name)
            
            # Update global settings for immediate use
            settings.input_dir = input_dir
            settings.output_dir = output_dir
            settings.stamp_pic_name = pic_name
            
            # Save network settings to QSettings as backup
            self._save_network_settings_to_qsettings()
            
            self.settings.sync()
            self.logger.debug("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    def _load_network_settings_from_qsettings(self):
        """Load network settings from QSettings as backup if not already set in settings object."""
        import os
        
        # Only use QSettings values if environment variables are not set
        # This preserves the priority: .env file > environment variables > QSettings > defaults
        
        if not os.getenv('SSL_VERIFY') and hasattr(settings, 'ssl_verify'):
            saved_ssl_verify = self.settings.value("network/ssl_verify", None)
            if saved_ssl_verify is not None:
                settings.ssl_verify = saved_ssl_verify == 'true'
                os.environ['SSL_VERIFY'] = saved_ssl_verify
        
        if not os.getenv('USE_CERTIFI') and hasattr(settings, 'use_certifi'):
            saved_use_certifi = self.settings.value("network/use_certifi", None)
            if saved_use_certifi is not None:
                settings.use_certifi = saved_use_certifi == 'true'
                os.environ['USE_CERTIFI'] = saved_use_certifi
        
        if not os.getenv('DISABLE_SSL_WARNINGS') and hasattr(settings, 'disable_ssl_warnings'):
            saved_disable_ssl_warnings = self.settings.value("network/disable_ssl_warnings", None)
            if saved_disable_ssl_warnings is not None:
                settings.disable_ssl_warnings = saved_disable_ssl_warnings == 'true'
                os.environ['DISABLE_SSL_WARNINGS'] = saved_disable_ssl_warnings
        
        if not os.getenv('SSL_CERT_FILE') and hasattr(settings, 'ssl_cert_file'):
            saved_ssl_cert_file = self.settings.value("network/ssl_cert_file", None)
            if saved_ssl_cert_file:
                settings.ssl_cert_file = saved_ssl_cert_file
                os.environ['SSL_CERT_FILE'] = saved_ssl_cert_file
        
        if not os.getenv('HTTP_PROXY') and hasattr(settings, 'http_proxy'):
            saved_http_proxy = self.settings.value("network/http_proxy", None)
            if saved_http_proxy:
                settings.http_proxy = saved_http_proxy
                os.environ['HTTP_PROXY'] = saved_http_proxy
        
        if not os.getenv('HTTPS_PROXY') and hasattr(settings, 'https_proxy'):
            saved_https_proxy = self.settings.value("network/https_proxy", None)
            if saved_https_proxy:
                settings.https_proxy = saved_https_proxy
                os.environ['HTTPS_PROXY'] = saved_https_proxy
    
    def _save_network_settings_to_qsettings(self):
        """Save current network settings to QSettings as backup."""
        # Save network settings that are currently active
        self.settings.setValue("network/ssl_verify", 'true' if getattr(settings, 'ssl_verify', True) else 'false')
        self.settings.setValue("network/use_certifi", 'true' if getattr(settings, 'use_certifi', True) else 'false')
        self.settings.setValue("network/disable_ssl_warnings", 'true' if getattr(settings, 'disable_ssl_warnings', False) else 'false')
        
        if hasattr(settings, 'ssl_cert_file') and settings.ssl_cert_file:
            self.settings.setValue("network/ssl_cert_file", settings.ssl_cert_file)
        else:
            self.settings.remove("network/ssl_cert_file")
        
        if hasattr(settings, 'http_proxy') and settings.http_proxy:
            self.settings.setValue("network/http_proxy", settings.http_proxy)
        else:
            self.settings.remove("network/http_proxy")
        
        if hasattr(settings, 'https_proxy') and settings.https_proxy:
            self.settings.setValue("network/https_proxy", settings.https_proxy)
        else:
            self.settings.remove("network/https_proxy")
    
    
    def update_ui_state(self, processing: bool = False):
        """Update UI state based on processing status."""
        self.start_button.setEnabled(not processing)
        self.stop_button.setEnabled(processing)
        self.pause_processing_btn.setEnabled(processing)
        self.input_dir_edit.setEnabled(not processing)
        self.output_dir_edit.setEnabled(not processing)
        
        if processing:
            if self.is_processing_paused:
                self.status_label.setText("Paused")
                self.status_label.setStyleSheet("font-weight: bold; color: orange;")
            else:
                self.status_label.setText("Processing...")
                self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        else:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
            self.current_file_label.setText("None")
            self.progress_bar.setValue(0)
            self.is_processing_paused = False
            self.pause_processing_btn.setText("Pause Processing")
    
    # Event handlers
    def browse_input_directory(self):
        """Browse for input directory."""
        current_path = self.input_dir_edit.text()
        if current_path and not Path(current_path).is_absolute():
            # Convert relative path to absolute for dialog starting point
            current_path = str(self.project_root / current_path)
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select Input Directory", current_path
        )
        if directory:
            # Convert to relative path for display
            relative_path = get_relative_path(directory, self.project_root)
            self.input_dir_edit.setText(relative_path)
            
            # Update tooltip with full path (normalized for display)
            self.input_dir_edit.setToolTip(f"Full path: {normalize_path_display(directory)}")
    
    def browse_output_directory(self):
        """Browse for output directory."""
        current_path = self.output_dir_edit.text()
        if current_path and not Path(current_path).is_absolute():
            # Convert relative path to absolute for dialog starting point  
            current_path = str(self.project_root / current_path)
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", current_path
        )
        if directory:
            # Convert to relative path for display
            relative_path = get_relative_path(directory, self.project_root)
            self.output_dir_edit.setText(relative_path)
            
            # Update tooltip with full path (normalized for display)
            self.output_dir_edit.setToolTip(f"Full path: {normalize_path_display(directory)}")
    
    def get_absolute_path(self, relative_or_absolute_path: str) -> Path:
        """Convert relative path to absolute path based on project root."""
        path = Path(relative_or_absolute_path)
        if path.is_absolute():
            return path
        else:
            return self.project_root / path
    
    def show_settings_dialog(self):
        """Show the advanced settings dialog."""
        dialog = ConfigDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Reload only config-related settings, preserve directories
            self.reload_config_settings()
    
    def show_user_guide(self):
        """Show the user guide help dialog."""
        try:
            help_dialog = HelpDialog(self)
            help_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error showing user guide: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open user guide:\n{str(e)}"
            )
    
    def show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, 
            "About Invoice Reconciliator",
            f"Invoice Reconciliator v{get_application_version()}\n\n"
            "An automated tool for processing and validating invoices\n"
            "against purchase orders using AI technology.\n\n"
            "© 2025 KDDI Corporation"
        )
    
    def show_available_styles(self):
        """Show available Qt styles for debugging."""
        try:
            app: QApplication = QApplication.instance()
            available_styles = self.get_available_themes()
            
            # Get current style
            current_style = app.style().objectName()
            
            styles_text = f"Current Style: {current_style}\n\n"
            styles_text += "Available Styles:\n"
            
            if available_styles:
                for style in sorted(available_styles.keys()):
                    styles_text += f"• {style}\n"
            else:
                styles_text += "• No styles detected (using fallback detection)\n"
            
            QMessageBox.information(
                self,
                "Available Qt Styles",
                styles_text
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not retrieve style information:\n{str(e)}"
            )
    
    def start_processing(self):
        """Start the PDF processing."""
        # Validate API key first
        if not settings.validate_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                settings.get_api_key_error()
            )
            # Open settings dialog to help user configure API key
            self.show_settings_dialog()
            return
        
        # Validate inputs - convert relative paths to absolute
        input_path_text = self.input_dir_edit.text().strip()
        input_dir = self.get_absolute_path(input_path_text)
        
        if not input_dir.exists():
            QMessageBox.warning(
                self, 
                "Invalid Input", 
                f"Input directory does not exist:\n{input_dir}\n\n"
                f"Please select a valid input directory."
            )
            return
        
        # Check if input directory contains PDF files
        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            QMessageBox.warning(
                self, 
                "No PDF Files", 
                f"No PDF files found in the selected directory:\n{input_dir}\n\n"
                "Please select a directory containing PDF files to process."
            )
            return
        
        output_path_text = self.output_dir_edit.text().strip()
        output_dir = self.get_absolute_path(output_path_text)
        
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Output Directory Error", 
                    f"Could not create output directory:\n{output_dir}\n\nError: {str(e)}"
                )
                return
        
        # Validate PIC name
        pic_name = self.pic_name_edit.text().strip()
        if not pic_name:
            reply = QMessageBox.question(
                self,
                "Missing PIC Name",
                "PIC name is empty. Do you want to continue without stamping?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Update settings with current values
        settings.stamp_pic_name = pic_name
        
        try:
            # Show processing confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Processing",
                f"Ready to process {len(pdf_files)} PDF files:\n\n"
                f"Input: {input_path_text}\n"
                f"Output: {output_path_text}\n"
                f"PIC Name: {pic_name or 'None (no stamping)'}\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Initialize engine
            from ..utils import get_timestamp
            self.output_dir = output_dir / get_timestamp()
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            self.engine = InvoiceReconciliationEngine(self.output_dir)
            self.engine.initialize()
            
            # Clear previous results
            self.result_table.setRowCount(0)
            self.result_data.clear()  # Clear stored result data
            self._resize_table_to_fit_content()  # Reset table size
            
            # Log processing start info - these will be captured by the permanent log handler
            self.logger.info("=== Processing Started ===")
            self.logger.info(f"Input directory: {input_dir}")
            self.logger.info(f"Output directory: {self.output_dir}")
            self.logger.info(f"Found {len(pdf_files)} PDF files")
            
            # Start processing thread
            self.processing_thread = ProcessingThread(self.engine, input_dir)
            self.processing_thread.progress_updated.connect(self.on_progress_updated)
            self.processing_thread.file_started.connect(self.on_file_started)
            self.processing_thread.file_completed.connect(self.on_file_completed)
            self.processing_thread.workflow_completed.connect(self.on_workflow_completed)
            # Note: log_message connection removed - using permanent log handler instead
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()
            
            self.update_ui_state(processing=True)
            self.logger.info("Processing started from GUI")
            
        except Exception as e:
            error_msg = f"Failed to start processing: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.logger.error(error_msg, exc_info=True)
    
    def stop_processing(self):
        """Stop the PDF processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait(5000)  # Wait up to 5 seconds
            
        self.update_ui_state(processing=False)
        self.logger.info("Processing stopped by user")
    
    def toggle_processing_pause(self):
        """Toggle pause/resume for processing workflow."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.is_processing_paused = not self.is_processing_paused
            
            if self.is_processing_paused:
                self.pause_processing_btn.setText("Resume Processing")
                self.processing_thread.pause()
                self.logger.info("Processing paused by user")
            else:
                self.pause_processing_btn.setText("Pause Processing")
                self.processing_thread.resume()
                self.logger.info("Processing resumed by user")
            
            # Update UI state to reflect pause status
            self.update_ui_state(processing=True)
    
    def import_results(self):
        """Import existing JSON result files from a folder."""
        try:
            folder_path = QFileDialog.getExistingDirectory(
                self,
                "Select folder containing JSON result files",
                str(self.project_root / "data" / "output"),
            )
            
            if not folder_path:
                return
            
            folder = Path(folder_path)
            json_files = list(folder.rglob("*.json"))
            
            if not json_files:
                QMessageBox.information(
                    self, 
                    "No Files Found", 
                    f"No JSON files found in the selected folder:\n{folder}"
                )
                return
            
            # Clear current results
            self.result_data.clear()
            self.result_table.setRowCount(0)
            self._resize_table_to_fit_content()  # Reset table size
            
            imported_count = 0
            failed_count = 0
            
            for json_file in json_files:
                result_data = load_json(json_file)

                if result_data is not None:
                    # Extract filename for the key (without .json extension)
                    filename = json_file.stem

                    # Store the result data
                    self.result_data[filename] = result_data
                
                    # Add to table
                    self.add_result_to_table(result_data)
                    imported_count += 1
                else:
                    failed_count += 1
            
            # Show success message
            message = f"Successfully imported {imported_count} result files"
            if failed_count > 0:
                message += f" ({failed_count} files failed to import)"
            
            QMessageBox.information(self, "Import Complete", message)
            self.logger.info(f"Imported {imported_count} results from {folder}")
            
            # Log import completion - this will be captured by the permanent log handler
            self.logger.info(f"Imported {imported_count} result files")
            
        except Exception as e:
            error_msg = f"Error importing results: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Import Error", error_msg)
    
    def closeEvent(self, event):
        """Handle application close event with proper cleanup."""
        try:
            self.logger.info("Application shutting down...")
            
            # Stop any running processing
            if self.processing_thread and self.processing_thread.isRunning():
                self.logger.info("Stopping processing thread...")
                self.processing_thread.terminate()
                if not self.processing_thread.wait(3000):  # Wait 3 seconds
                    self.logger.warning("Processing thread did not stop gracefully")
                    self.processing_thread.kill()
            
            # Stop any running retry processing
            if self.retry_thread and self.retry_thread.isRunning():
                self.logger.info("Stopping retry thread...")
                self.retry_thread.terminate()
                if not self.retry_thread.wait(3000):  # Wait 3 seconds
                    self.logger.warning("Retry thread did not stop gracefully")
                    self.retry_thread.kill()
            
            # Save settings
            self.save_settings()
            
            # Clean up engine resources
            if self.engine:
                self.logger.debug("Cleaning up engine resources")
                del self.engine
                self.engine = None
            
            self.logger.info("Application shutdown complete")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            event.accept()  # Accept anyway to prevent hanging
    
    def show_not_implemented_dialog(self, feature_name: str, description: str = ""):
        """Show a dialog for features that are not yet implemented."""
        full_description = f"The '{feature_name}' feature is not implemented yet."
        if description:
            full_description += f"\n\n{description}"
        full_description += "\n\nThis feature may be added in future versions if requested by users."
        
        QMessageBox.information(
            self,
            "Feature Not Implemented",
            full_description
        )

    def get_result_issues(self, result: dict) -> list[str]:
        """Get the list of validation issues from a processing result."""
        return result.get('validation_result', {}).get('issues', [])

    def get_result_status(self, result: dict) -> str:
        """Get the status of a processing result."""
        # Status with color coding (check multiple possible field names)
        status = result.get('approval_status', result.get('status', None))
        
        # Handle validation failures and empty status
        if not status or str(status).lower() in ['none', 'failed']:
            # Check if there's an error or failure indicated
            if result.get('error_message') or result.get('error_details') or result.get('status') == 'failed':
                return 'FAILED'
            issues_count = len(self.get_result_issues(result))
            if issues_count > 0:
                status = 'REQUIRES REVIEW'
            else:
                status = 'UNKNOWN'
        return status

    def open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.output_dir and self.output_dir.exists():
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(self.output_dir)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.output_dir)])
    
    # Processing callbacks
    def on_progress_updated(self, progress: dict):
        """Handle progress update."""
        try:
            progress_percent = progress.get('progress_percent', 0)
            self.progress_bar.setValue(int(progress_percent))
            
            processed = progress.get('processed_files', 0)
            total = progress.get('total_files', 0)
            current_status = progress.get('current_status', 'Processing')
            
            # Update status bar with detailed information
            status_msg = f"{current_status}: {processed}/{total} files ({progress_percent:.1f}%)"
            self.statusBar().showMessage(status_msg)
            
            # Update current file if available
            current_file = progress.get('current_file', '')
            if current_file:
                filename = Path(current_file).name
                self.current_file_label.setText(filename)
                
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
    
    def on_file_started(self, result: dict):
        """Handle file processing start."""
        try:
            filename = Path(result.get('pdf_path', 'Unknown')).name
            self.current_file_label.setText(filename)
            
            # Log message will be handled by the permanent log capture, no need to add manually
            self.logger.info(f"Started processing: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error handling file started: {e}")
    
    def on_file_completed(self, result: dict):
        """Handle file processing completion."""
        try:
            filename = Path(result.get('pdf_path', 'Unknown')).name
            status = self.get_result_status(result)

            # Log message will be handled by the permanent log capture, no need to add manually
            self.logger.info(f"Completed processing: {filename} - {status}")
            
            # Add to results table
            self.add_result_to_table(result)
            
        except Exception as e:
            self.logger.error(f"Error handling file completed: {e}")
    
    def on_workflow_completed(self, summary: dict):
        """Handle workflow completion."""
        try:
            self.update_ui_state(processing=False)
            
            completed = summary.get('completed_files', 0)
            failed = summary.get('failed_files', 0)
            total = summary.get('total_files', 0)
            success_rate = summary.get('success_rate', 0)
            
            # Log completion info - these will be captured by the permanent log handler
            self.logger.info("=== Processing Completed ===")
            self.logger.info(f"Total: {total}, Success: {completed}, Failed: {failed}")
            self.logger.info(f"Success rate: {success_rate:.1f}%")
            
            # Show completion dialog
            completion_msg = (
                f"Processing completed!\n\n"
                f"Total files: {total}\n"
                f"Successful: {completed}\n"
                f"Failed: {failed}\n"
                f"Success rate: {success_rate:.1f}%"
            )
            
            if failed == 0:
                QMessageBox.information(self, "Processing Complete", completion_msg)
            else:
                completion_msg += f"\n\nSome files failed to process. Check the logs and results for details."
                QMessageBox.warning(self, "Processing Complete (with errors)", completion_msg)
            
            # Cleanup
            if self.engine:
                self.engine.cleanup()
                
        except Exception as e:
            self.logger.error(f"Error handling workflow completion: {e}")
    
    def on_log_message(self, level: str, message: str):
        """Handle log message."""
        try:
            if self.log_viewer:
                self.log_viewer.add_log_message(level, message)
        except Exception as e:
            self.logger.error(f"Error displaying log message: {e}")
    
    def on_error_occurred(self, error: str):
        """Handle processing error."""
        try:
            self.update_ui_state(processing=False)
            
            error_msg = f"An error occurred during processing:\n\n{error}"
            
            # Log error - this will be captured by the permanent log handler
            self.logger.error(f"Processing error: {error}")
            
            # Show error dialog with options
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Processing Error")
            msg_box.setText("Processing failed with an error.")
            msg_box.setDetailedText(error_msg)
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Retry
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
            
            result = msg_box.exec()
            if result == QMessageBox.StandardButton.Retry:
                # Offer to retry processing
                self.retry_processing()
            
            self.logger.error(f"Processing error: {error}")
            
        except Exception as e:
            self.logger.error(f"Error handling processing error: {e}")
    
    def add_result_to_table(self, result: dict):
        """Add a processing result to the results table."""
        try:
            self.logger.debug(f"Adding result to table: {result}")
            
            row_count = self.result_table.rowCount()
            self.result_table.insertRow(row_count)
            
            # File name
            filename = Path(result.get('pdf_path', 'Unknown')).name
            self.result_table.setItem(row_count, 0, QTableWidgetItem(filename))
            
            # Store the result data for later access using filename as key
            self.result_data[filename] = result
            self.logger.debug(f"Stored result data for {filename}")

            # Status with color coding (check multiple possible field names)
            status = self.get_result_status(result)

            self.logger.debug(f"Status for {filename}: {status}")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Apply theme-aware colors
            is_dark = self._detect_dark_mode()
            self._apply_status_colors(status_item, status, is_dark)
            
            self.result_table.setItem(row_count, 1, status_item)
            
            # Issues count (check multiple possible field names)
            issues_count = len(self.get_result_issues(result))
            if issues_count is None or issues_count == 0:
                # Try alternative field names
                if 'validation_issues' in result and isinstance(result['validation_issues'], list):
                    issues_count = len(result['validation_issues'])
                
            self.logger.debug(f"Issues count for {filename}: {issues_count}")
            
            issues_item = QTableWidgetItem(str(issues_count))
            issues_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Apply theme-aware colors for issues column
            self._apply_issues_colors(issues_item, issues_count, is_dark)
            
            self.result_table.setItem(row_count, 2, issues_item)
            
            # Actions - create action buttons widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            
            self.logger.debug(f"Creating action buttons for {filename}")
            
            # View button (always available)
            view_btn = QPushButton("View")
            view_btn.setToolTip("View detailed processing results and validation report")
            view_btn.setMaximumHeight(25)
            view_btn.clicked.connect(lambda checked, r=row_count: self.view_result_details(r))
            actions_layout.addWidget(view_btn)
            
            # PDF button (if PDF exists)
            pdf_path = result.get('processed_pdf_path') or result.get('pdf_path')
            if pdf_path:
                pdf_btn = QPushButton("PDF")
                pdf_btn.setToolTip("Open the processed PDF file")
                pdf_btn.setMaximumHeight(25)
                pdf_btn.clicked.connect(lambda checked, r=row_count: self.open_pdf(r))
                actions_layout.addWidget(pdf_btn)
                self.logger.debug(f"Added PDF button for {filename}")
            
            # Retry button (if failed)
            if status in ['FAILED', 'failed']:
                retry_btn = QPushButton("Retry")
                retry_btn.setToolTip("Retry processing this failed file")
                retry_btn.setMaximumHeight(25)
                # Use default theme styling (removed custom background color)
                retry_btn.clicked.connect(lambda checked, r=row_count: self.retry_processing(r))
                actions_layout.addWidget(retry_btn)
                self.logger.debug(f"Added Retry button for {filename}")
            
            actions_layout.addStretch()
            self.result_table.setCellWidget(row_count, 3, actions_widget)
            
            self.logger.debug(f"Successfully added {filename} to table at row {row_count}")
            
            # Auto-scroll to new row
            self.result_table.scrollToBottom()
            
            # Resize table to fit new content
            self._resize_table_to_fit_content()
            
        except Exception as e:
            self.logger.error(f"Error adding result to table: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def view_result_details(self, row: int):
        """View detailed results for a specific row."""
        try:
            # Get filename from the table
            filename_item = self.result_table.item(row, 0)
            if not filename_item:
                return
            
            filename = filename_item.text()
            
            # Get stored result data
            if filename not in self.result_data:
                QMessageBox.warning(
                    self, 
                    "Result Not Found", 
                    f"No stored result data found for \"{filename}\""
                )
                return
            
            result_data = self.result_data[filename]
            result_json_path = result_data.get('result_json_path')
            
            if result_json_path and Path(result_json_path).exists():
                # Open detailed result viewer with the correct path
                viewer = ResultDetailViewer(Path(result_json_path), self)
                # Use show() instead of exec() to prevent modal dialog issues
                viewer.show()
                # Keep a reference to prevent garbage collection
                if not hasattr(self, '_open_viewers'):
                    self._open_viewers = []
                self._open_viewers.append(viewer)
                
                # Clean up closed viewers
                self._open_viewers = [v for v in self._open_viewers if v.isVisible()]
            else:
                QMessageBox.warning(
                    self, 
                    "Result File Not Found", 
                    f"Could not find result file for \"{filename}\"\n"
                    f"Expected path: {result_json_path}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to view result details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to view result details:\n{str(e)}")
    
    def open_pdf(self, row: int):
        """Open PDF file for a specific row."""
        try:
            # Get filename from the table
            filename_item = self.result_table.item(row, 0)
            if not filename_item:
                return
            
            filename = filename_item.text()
            
            # Get stored result data
            if filename not in self.result_data:
                QMessageBox.warning(
                    self, 
                    "Result Not Found", 
                    f"No stored result data found for \"{filename}\""
                )
                return
            
            result_data = self.result_data[filename]
            
            # Try processed PDF path first, then original PDF path
            pdf_path = result_data.get('processed_pdf_path') or result_data.get('pdf_path')
            
            if pdf_path and Path(pdf_path).exists():
                # Open with system default PDF viewer
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    # Use os.startfile for Windows for better compatibility
                    import os
                    os.startfile(str(pdf_path))
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', str(pdf_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(pdf_path)])
                    
                self.logger.info(f"Opened PDF: {pdf_path}")
            else:
                QMessageBox.warning(
                    self, 
                    "PDF Not Found", 
                    f"Could not find PDF file for \"{filename}\"\n"
                    f"Expected path: {pdf_path}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to open PDF: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open PDF:\n{str(e)}")
    
    def retry_processing(self, row: int):
        """Retry processing for a specific row."""
        try:
            # Get filename from the table
            filename_item = self.result_table.item(row, 0)
            if not filename_item:
                return
            
            filename = filename_item.text()
            
            # Get stored result data to find the original PDF path
            if filename not in self.result_data:
                QMessageBox.warning(
                    self, 
                    "Result Not Found", 
                    f"No stored result data found for \"{filename}\""
                )
                return
            
            result_data = self.result_data[filename]
            original_pdf_path = result_data.get('pdf_path')
            
            if not original_pdf_path or not Path(original_pdf_path).exists():
                QMessageBox.warning(
                    self, 
                    "PDF Not Found", 
                    f"Original PDF file not found for \"{filename}\"\n"
                    f"Expected path: {original_pdf_path}"
                )
                return
            
            reply = QMessageBox.question(
                self, 
                "Retry Processing",
                f"Are you sure you want to retry processing for {filename}?\n\n"
                f"This will reprocess the file with current settings and generate a new result.\n"
                f"The original result will be preserved for comparison.\n\n"
                f"The new result will be saved as: {Path(filename).stem}_retry_X.json",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._retry_single_file(Path(original_pdf_path), filename)
                
        except Exception as e:
            self.logger.error(f"Failed to retry processing: {e}")
            QMessageBox.critical(self, "Error", f"Failed to retry processing:\n{str(e)}")
    
    def _retry_single_file(self, pdf_path: Path, original_filename: str):
        """Retry processing a single file in the background."""
        try:
            # Ensure engine is present
            if not self.engine:
                # Create new engine if not available
                from ..core import InvoiceReconciliationEngine
                self.engine = InvoiceReconciliationEngine(self.output_dir)
            
            # Update UI to show retry in progress
            self.statusBar().showMessage(f"Retrying processing for {original_filename}...")
            
            # Log message will be handled by the permanent log capture, no need to add manually
            self.logger.info(f"Starting retry for {original_filename}")
            
            # Create a background thread for retry processing using the imported RetryThread
            # Start retry thread
            self.retry_thread = RetryThread(self.engine, pdf_path)
            self.retry_thread.completed.connect(self._on_retry_completed)
            self.retry_thread.error_occurred.connect(self._on_retry_error)
            self.retry_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start retry processing: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start retry processing:\n{str(e)}")
            self.statusBar().showMessage("Ready")
    
    def _on_retry_completed(self, result_dict: dict):
        """Handle completion of retry processing."""
        try:
            filename = Path(result_dict.get('pdf_path', 'Unknown')).name
            status = self.get_result_status(result_dict)
            
            # Update status and show success message
            self.statusBar().showMessage("Ready")
            
            # Log message will be handled by the permanent log capture, no need to add manually
            self.logger.info(f"Retry completed for {filename}: {status}")
            
            # Show success dialog
            retry_result_file = result_dict.get('result_json_path', 'Unknown')
            QMessageBox.information(
                self,
                "Retry Complete",
                f"Retry processing completed for {filename}\n\n"
                f"Status: {status}\n"
                f"Result saved to: {Path(retry_result_file).name if retry_result_file != 'Unknown' else 'Unknown'}"
            )
            
            # Cleanup
            if self.engine:
                self.engine.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error handling retry completion: {e}")
            self.statusBar().showMessage("Ready")
    
    def _on_retry_error(self, error_message: str):
        """Handle error in retry processing."""
        try:
            self.logger.error(f"Retry processing failed: {error_message}")
            self.statusBar().showMessage("Ready")
            
            # Log message will be handled by the permanent log capture, no need to add manually
            
            QMessageBox.critical(
                self,
                "Retry Failed",
                f"Failed to retry processing:\n\n{error_message}"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling retry error: {e}")
            self.statusBar().showMessage("Ready")
    
    def on_result_double_clicked(self, index):
        """Handle double-click on result table."""
        if index.isValid():
            self.view_result_details(index.row())
    
    def refresh_results(self):
        """Refresh the results table."""
        try:
            if not self.engine or not hasattr(self.engine, 'get_workflow_results'):
                return
            
            # Clear current table
            self.result_table.setRowCount(0)
            self.result_data.clear()  # Also clear the stored result data
            
            # Get results from engine
            results = self.engine.get_workflow_results()
            
            # Re-populate table
            for result in results:
                self.add_result_to_table(result.model_dump() if hasattr(result, 'model_dump') else result)
            
            # Resize table to fit new content
            self._resize_table_to_fit_content()
            
            self.logger.info("Results table refreshed")
                
        except Exception as e:
            self.logger.error(f"Error refreshing results: {e}")
    
    def export_results(self):
        """Export processing results."""
        try:
            if self.result_table.rowCount() == 0:
                QMessageBox.information(self, "No Results", "No results to export.")
                return
            
            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                f"processing_results_{Path(self.input_dir_edit.text()).name}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Export table data to CSV
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = []
                for col in range(self.result_table.columnCount()):
                    headers.append(self.result_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.result_table.rowCount()):
                    row_data = []
                    for col in range(self.result_table.columnCount()):
                        item = self.result_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"Results exported to:\n{file_path}")
            self.logger.info(f"Results exported to: {file_path}")
            
        except Exception as e:
            error_msg = f"Error exporting results: {str(e)}"
            QMessageBox.critical(self, "Export Error", error_msg)
            self.logger.error(error_msg)
    
    # Theme management methods
    def get_available_themes(self) -> dict:
        """Get available Qt themes/styles."""
        # Get actual available styles from Qt
        try:
            available_qt_styles = [s.lower() for s in QStyleFactory.keys()]
        except:
            # Fallback: common styles that usually work
            available_qt_styles = ['fusion', 'windows', 'windowsvista']
        
        # Basic themes that should work on most systems
        themes = {
            'Fusion (Modern)': 'fusion',
        }
        
        # Add platform-specific themes based on availability
        import platform
        if platform.system() == "Windows":
            potential_themes = {
                'Windows Vista': 'windowsvista',
                'Windows 11': 'windows11',
                'Windows (Classic)': 'windows',
            }
        elif platform.system() == "Darwin":  # macOS
            potential_themes = {
                'macOS': 'macos'
            }
        else:  # Linux and others
            potential_themes = {
                'GTK+': 'gtk'
            }
        
        # Add themes that are available
        for name, style in potential_themes.items():
            themes[name] = style  # Add all for now, Qt will handle unavailable ones
        
        return themes
    
    def setup_theme_menu(self, theme_menu: QMenu):
        """Set up the theme selection menu."""
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        
        available_themes = self.get_available_themes()
        current_theme = self.settings.value("theme", "Windows Vista")
        
        for theme_name, theme_style in available_themes.items():
            action = QAction(theme_name, self)
            action.setCheckable(True)
            action.setData(theme_style)
            
            # Check if this is the current theme
            if theme_name == current_theme:
                action.setChecked(True)
            
            # Connect to theme change handler
            action.triggered.connect(lambda checked, name=theme_name: self.change_theme(name))
            
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[theme_name] = action
    
    def change_theme(self, theme_name: str):
        """Change the application theme."""
        try:
            available_themes = self.get_available_themes()
            theme_style = available_themes.get(theme_name, '')
            
            app: QApplication = QApplication.instance()
            if app:
                if theme_style:
                    # Try to set the specific style
                    app.setStyle(theme_style)
                    self.logger.info(f"Theme changed to: {theme_name} ({theme_style})")
                else:
                    # Reset to system default
                    app.setStyle('')
                    self.logger.info(f"Theme reset to system default")
                
                # Save the theme preference
                self.settings.setValue("theme", theme_name)
                
                # Refresh log viewer theme and re-render all messages
                if hasattr(self, 'log_viewer') and self.log_viewer:
                    self.log_viewer.refresh_theme()
                
                # Refresh result table colors for the new theme
                if hasattr(self, 'result_table') and self.result_table.rowCount() > 0:
                    self._refresh_result_table_colors()
                
                # Show confirmation message
                self.statusBar().showMessage(f"Theme changed to: {theme_name}", 3000)
                
        except Exception as e:
            self.logger.error(f"Failed to change theme to {theme_name}: {e}")
            QMessageBox.warning(
                self,
                "Theme Change Failed",
                f"Could not change theme to '{theme_name}'.\n"
                f"This theme may not be available on your system.\n\n"
                f"Error: {str(e)}"
            )
            
            # Revert to previous theme selection
            current_theme = self.settings.value("theme", "System Default")
            if current_theme in self.theme_actions:
                self.theme_actions[current_theme].setChecked(True)
    
    def load_theme(self):
        """Load the saved theme on application startup."""
        try:
            saved_theme = self.settings.value("theme", "System Default")
            self.logger.info(f"Loading saved theme: {saved_theme}")
            
            # Apply the theme without showing confirmation message
            available_themes = self.get_available_themes()
            theme_style = available_themes.get(saved_theme, '')
            
            app: QApplication = QApplication.instance()
            if app and theme_style:
                app.setStyle(theme_style)
                self.logger.info(f"Applied saved theme: {saved_theme} ({theme_style})")
                
                # Refresh theme for all components after theme is applied
                if hasattr(self, 'log_viewer') and self.log_viewer:
                    QTimer.singleShot(100, self.log_viewer.refresh_theme)  # Delay to ensure theme is applied
                    
        except Exception as e:
            self.logger.warning(f"Failed to load saved theme: {e}")
    
    def reset_window_layout(self):
        """Reset the window layout to default."""
        try:
            # Reset window size
            self.resize(800, 600)
            
            # Reset splitter sizes
            # Find and reset all splitters
            splitters = self.findChildren(QSplitter)
            for splitter in splitters:
                if splitter.orientation() == Qt.Orientation.Horizontal:
                    splitter.setSizes([400, 400])
                else:  # Vertical
                    splitter.setSizes([300, 250])
            
            self.statusBar().showMessage("Window layout reset to default", 3000)
            self.logger.info("Window layout reset to default")
            
        except Exception as e:
            self.logger.error(f"Failed to reset window layout: {e}")
    
    def refresh_view(self):
        """Refresh the current view."""
        try:
            # Refresh results table
            self.refresh_results()
            
            # Update status
            self.statusBar().showMessage("View refreshed", 2000)
            self.logger.info("View refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh view: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Processing is still running. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_processing()
            else:
                event.ignore()
                return
        
        # Save settings before closing
        self.save_settings()
        
        if self.engine:
            self.engine.cleanup()
        
        event.accept()
