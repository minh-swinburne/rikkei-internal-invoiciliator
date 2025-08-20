"""
Main window for the invoice reconciliation GUI application.
"""

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
from PySide6.QtGui import QAction, QFont, QIcon, QActionGroup

from .config_dialog import ConfigDialog
from .log_viewer import LogViewer
from .result_viewer import ResultViewer
from .qt_logging import QtLogHandler, LogCapture
from ..core import InvoiceReconciliationEngine
from ..settings import settings
from ..logging_config import get_module_logger
from ..utils import get_relative_path, get_project_root, normalize_path_display


class ProcessingThread(QThread):
    """Background thread for processing PDFs."""
    
    progress_updated = Signal(dict)
    file_started = Signal(dict)
    file_completed = Signal(dict)
    workflow_completed = Signal(dict)
    log_message = Signal(str, str)  # level, message
    error_occurred = Signal(str)
    
    def __init__(self, engine: InvoiceReconciliationEngine, input_dir: Path):
        super().__init__()
        self.engine = engine
        self.input_dir = input_dir
        self.should_stop = False
        
        # Set up logging capture
        self.log_handler = QtLogHandler()
        self.log_handler.log_message.connect(self.log_message)
        self.log_capture = LogCapture(self.log_handler)
    
    def run(self):
        """Run the processing in background thread."""
        try:
            # Start log capture for real-time GUI updates
            with self.log_capture:
                # Set up progress callbacks
                self.engine.on_progress_update = self.emit_progress_update
                self.engine.on_file_started = self.emit_file_started
                self.engine.on_file_completed = self.emit_file_completed
                self.engine.on_workflow_completed = self.emit_workflow_completed
                
                # Emit startup message
                self.log_message.emit("INFO", f"Starting processing of directory: {self.input_dir}")
                
                # Start workflow
                workflow = self.engine.start_workflow(self.input_dir)
                
                if workflow.total_files == 0:
                    self.log_message.emit("WARNING", "No PDF files found in input directory")
                    return
                
                self.log_message.emit("INFO", f"Found {workflow.total_files} PDF files to process")
                
                # Process files
                self.engine.process_workflow()
                
        except Exception as e:
            self.log_message.emit("ERROR", f"Processing failed: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def emit_progress_update(self, progress: dict):
        """Emit progress update with error handling."""
        try:
            self.progress_updated.emit(progress)
        except Exception as e:
            print(f"Error emitting progress update: {e}")
    
    def emit_file_started(self, result):
        """Emit file started signal with error handling."""
        try:
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
            self.file_started.emit(result_dict)
        except Exception as e:
            print(f"Error emitting file started: {e}")
    
    def emit_file_completed(self, result):
        """Emit file completed signal with error handling."""
        try:
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
            self.file_completed.emit(result_dict)
        except Exception as e:
            print(f"Error emitting file completed: {e}")
    
    def emit_workflow_completed(self, workflow):
        """Emit workflow completed signal with error handling."""
        try:
            summary = workflow.get_summary() if hasattr(workflow, 'get_summary') else workflow
            self.workflow_completed.emit(summary)
        except Exception as e:
            print(f"Error emitting workflow completed: {e}")
    
    def stop(self):
        """Request to stop processing."""
        self.should_stop = True
        self.log_message.emit("INFO", "Stop requested by user")
        if self.engine:
            try:
                self.engine.cancel_workflow()
                self.log_message.emit("INFO", "Processing cancelled")
            except Exception as e:
                self.log_message.emit("ERROR", f"Error during cancellation: {e}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_module_logger('gui.main_window')
        
        # Project root for relative path calculations
        self.project_root = get_project_root()
        
        # Core components
        self.engine: Optional[InvoiceReconciliationEngine] = None
        self.processing_thread: Optional[ProcessingThread] = None
        self.output_dir: Optional[Path] = None
        
        # UI components
        self.input_dir_edit: Optional[QLineEdit] = None
        self.output_dir_edit: Optional[QLineEdit] = None
        self.pic_name_edit: Optional[QLineEdit] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.status_label: Optional[QLabel] = None
        self.current_file_label: Optional[QLabel] = None
        self.start_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.log_viewer: Optional[LogViewer] = None
        self.result_table: Optional[QTableWidget] = None
        
        # Theme management
        self.theme_actions: dict = {}
        self.theme_group: Optional[QActionGroup] = None
        self.settings = QSettings()
        
        self.setup_ui()
        self.setup_menu()
        self.load_settings()
        self.load_theme()
        self.update_ui_state()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Invoice Reconciliation Tool")
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        
        # Set window icon
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
            except Exception:
                # Silently ignore icon loading errors
                pass
        
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
        layout.addWidget(self.input_dir_edit, 0, 1)
        
        input_browse_btn = QPushButton("Browse")
        input_browse_btn.clicked.connect(self.browse_input_directory)
        layout.addWidget(input_browse_btn, 0, 2)
        
        # Output directory
        layout.addWidget(QLabel("Output Directory:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output folder...")
        layout.addWidget(self.output_dir_edit, 1, 1)
        
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_output_directory)
        layout.addWidget(output_browse_btn, 1, 2)
        
        # PIC Name
        layout.addWidget(QLabel("PIC Name:"), 2, 0)
        self.pic_name_edit = QLineEdit()
        self.pic_name_edit.setText(settings.stamp_pic_name)
        layout.addWidget(self.pic_name_edit, 2, 1, 1, 2)
        
        # Settings button
        settings_btn = QPushButton("Advanced Settings...")
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
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_logs_btn)
        
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
        
        # Set column widths
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self.result_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_results)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(export_btn)
        
        open_output_btn = QPushButton("Open Output Folder")
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
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        # Debug: Show available styles
        styles_action = QAction("Available Styles (Debug)", self)
        styles_action.triggered.connect(self.show_available_styles)
        help_menu.addAction(styles_action)
    
    def load_settings(self):
        """Load settings into the UI."""
        # Set default directories as relative paths
        self.input_dir_edit.setText("data/input")
        self.output_dir_edit.setText("data/output")
        
        # Set tooltips to show full paths
        input_full_path = self.project_root / "data/input" 
        output_full_path = self.project_root / "data/output"
        self.input_dir_edit.setToolTip(f"Full path: {input_full_path}")
        self.output_dir_edit.setToolTip(f"Full path: {output_full_path}")
        
        # Set PIC name from settings
        self.pic_name_edit.setText(settings.stamp_pic_name)
    
    def update_ui_state(self, processing: bool = False):
        """Update UI state based on processing status."""
        self.start_button.setEnabled(not processing)
        self.stop_button.setEnabled(processing)
        self.input_dir_edit.setEnabled(not processing)
        self.output_dir_edit.setEnabled(not processing)
        
        if processing:
            self.status_label.setText("Processing...")
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
            self.current_file_label.setText("None")
            self.progress_bar.setValue(0)
    
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
            # Reload settings if they were saved
            self.load_settings()
    
    def show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self, 
            "About Invoice Reconciliation Tool",
            "Invoice Reconciliation Tool v1.0.0\n\n"
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
            if self.log_viewer:
                self.log_viewer.add_log_message("INFO", "=== Processing Started ===")
                self.log_viewer.add_log_message("INFO", f"Input directory: {input_dir}")
                self.log_viewer.add_log_message("INFO", f"Output directory: {self.output_dir}")
                self.log_viewer.add_log_message("INFO", f"Found {len(pdf_files)} PDF files")
            
            # Start processing thread
            self.processing_thread = ProcessingThread(self.engine, input_dir)
            self.processing_thread.progress_updated.connect(self.on_progress_updated)
            self.processing_thread.file_started.connect(self.on_file_started)
            self.processing_thread.file_completed.connect(self.on_file_completed)
            self.processing_thread.workflow_completed.connect(self.on_workflow_completed)
            self.processing_thread.log_message.connect(self.on_log_message)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()
            
            self.update_ui_state(processing=True)
            self.logger.info("Processing started from GUI")
            
        except Exception as e:
            error_msg = f"Failed to start processing: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.logger.error(error_msg, exc_info=True)
            if self.log_viewer:
                self.log_viewer.add_log_message("ERROR", error_msg)
    
    def stop_processing(self):
        """Stop the PDF processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait(5000)  # Wait up to 5 seconds
            
        self.update_ui_state(processing=False)
        self.logger.info("Processing stopped by user")
    
    def clear_logs(self):
        """Clear the log viewer."""
        if self.log_viewer:
            self.log_viewer.clear()
    
    def refresh_results(self):
        """Refresh the results table."""
        # TODO: Implement results refresh
        pass
    
    def export_results(self):
        """Export processing results."""
        # TODO: Implement results export
        pass
    
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
            
            # Add to log
            if self.log_viewer:
                self.log_viewer.add_log_message("INFO", f"Started processing: {filename}")
            
            self.logger.info(f"Started processing: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error handling file started: {e}")
    
    def on_file_completed(self, result: dict):
        """Handle file processing completion."""
        try:
            filename = Path(result.get('pdf_path', 'Unknown')).name
            status = result.get('approval_status', 'Unknown')
            
            # Add to log with status
            if self.log_viewer:
                self.log_viewer.add_log_message("INFO", f"Completed: {filename} - {status}")
            
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
            
            # Add completion log
            if self.log_viewer:
                self.log_viewer.add_log_message("INFO", "=== Processing Completed ===")
                self.log_viewer.add_log_message("INFO", f"Total: {total}, Success: {completed}, Failed: {failed}")
                self.log_viewer.add_log_message("INFO", f"Success rate: {success_rate:.1f}%")
            
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
            print(f"Error displaying log message: {e}")
    
    def on_error_occurred(self, error: str):
        """Handle processing error."""
        try:
            self.update_ui_state(processing=False)
            
            error_msg = f"An error occurred during processing:\n\n{error}"
            
            # Add to log
            if self.log_viewer:
                self.log_viewer.add_log_message("ERROR", f"Processing error: {error}")
            
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
    
    def retry_processing(self):
        """Retry the last processing operation."""
        try:
            reply = QMessageBox.question(
                self,
                "Retry Processing",
                "Do you want to retry processing with the same settings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_processing()
                
        except Exception as e:
            self.logger.error(f"Error during retry: {e}")
    
    def add_result_to_table(self, result: dict):
        """Add a processing result to the results table."""
        try:
            row_count = self.result_table.rowCount()
            self.result_table.insertRow(row_count)
            
            # File name
            filename = Path(result.get('pdf_path', 'Unknown')).name
            self.result_table.setItem(row_count, 0, QTableWidgetItem(filename))

            # Status with color coding
            status = result.get('approval_status', 'Unknown')
            status_item = QTableWidgetItem(status)
            
            if status == 'APPROVED':
                status_item.setBackground(Qt.GlobalColor.lightGreen)
            elif status == 'REQUIRES REVIEW':
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif status == 'FAILED':
                status_item.setBackground(Qt.GlobalColor.lightGray)
            else:
                status_item.setBackground(Qt.GlobalColor.cyan)
            
            self.result_table.setItem(row_count, 1, status_item)
            
            # Issues count
            issues_count = result.get('validation_issues_count', 0)
            if 'validation_issues' in result and isinstance(result['validation_issues'], list):
                issues_count = len(result['validation_issues'])
            
            issues_item = QTableWidgetItem(str(issues_count))
            if issues_count > 0:
                issues_item.setBackground(Qt.GlobalColor.yellow)
            
            self.result_table.setItem(row_count, 2, issues_item)
            
            # Actions - create clickable buttons
            actions_text = "View"
            if result.get('output_pdf_path'):
                actions_text += " | PDF"
            if status == 'FAILED':
                actions_text += " | Retry"
                
            self.result_table.setItem(row_count, 3, QTableWidgetItem(actions_text))
            
            # Auto-scroll to new row
            self.result_table.scrollToBottom()
            
        except Exception as e:
            self.logger.error(f"Error adding result to table: {e}")
    
    def refresh_results(self):
        """Refresh the results table."""
        try:
            if not self.engine or not hasattr(self.engine, 'get_workflow_results'):
                return
            
            # Clear current table
            self.result_table.setRowCount(0)
            
            # Get results from engine
            results = self.engine.get_workflow_results()
            
            # Re-populate table
            for result in results:
                self.add_result_to_table(result.to_dict() if hasattr(result, 'to_dict') else result)
            
            self.logger.info("Results table refreshed")
            if self.log_viewer:
                self.log_viewer.add_log_message("INFO", "Results table refreshed")
                
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
                
                # Refresh log viewer theme
                if hasattr(self, 'log_viewer'):
                    self.log_viewer.refresh_theme()
                
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
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        if self.engine:
            self.engine.cleanup()
