"""
Log viewer widget for the invoice reconciliation GUI application.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QCheckBox, QComboBox, QLabel, QGroupBox, QFileDialog,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QFont, QColor, QTextCharFormat, QPalette

from ..logging_config import get_module_logger

try:
    import darkdetect
    DARKDETECT_AVAILABLE = True
except ImportError:
    DARKDETECT_AVAILABLE = False


class LogViewer(QGroupBox):
    """Log viewer widget with filtering and export capabilities."""
    
    def __init__(self, parent=None):
        super().__init__("Processing Logs", parent)
        self.logger = get_module_logger('gui.log_viewer')
        
        # Settings
        self.max_lines = 1000
        self.auto_scroll = True
        
        # Theme detection
        self._is_dark_mode = self._detect_dark_mode()
        
        self.setup_ui()
    
    def _detect_dark_mode(self) -> bool:
        """Detect if we're in dark mode using multiple methods."""        
        # Method 1: Check Qt palette
        try:
            app: QApplication = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                # If window background is darker than 128, assume dark mode
                return window_color.lightness() < 128
        except Exception:
            self.logger.warning("Failed to detect dark mode using Qt palette", exc_info=True)

        # Method 2: Try darkdetect if available
        if DARKDETECT_AVAILABLE:
            try:
                theme = darkdetect.theme()
                if theme == 'Dark':
                    return True
                elif theme == 'Light':
                    return False
            except Exception:
                self.logger.warning("Failed to detect dark mode using darkdetect", exc_info=True)

        # Method 3: Check current theme name (fallback)
        try:
            app: QApplication = QApplication.instance()
            if app:
                style_name = app.style().objectName().lower()
                # Some known dark themes
                dark_themes = ['fusion', 'windows11', 'windows', 'darkstyle']
                if any(dark in style_name for dark in dark_themes):
                    return True
                # Windows Vista is always light
                if 'vista' in style_name or 'windowsvista' in style_name:
                    return False
        except Exception:
            self.logger.warning("Failed to detect dark mode using current theme", exc_info=True)

        # Default to light mode
        return False
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Log level filter
        control_layout.addWidget(QLabel("Level:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("INFO")
        self.level_filter.currentTextChanged.connect(self.filter_logs)
        control_layout.addWidget(self.level_filter)
        
        control_layout.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.toggled.connect(self.toggle_auto_scroll)
        control_layout.addWidget(self.auto_scroll_cb)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        control_layout.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_logs)
        control_layout.addWidget(export_btn)
        
        layout.addLayout(control_layout)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # Set monospace font for better readability
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.log_text.setFont(font)
        
        layout.addWidget(self.log_text)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.line_count_label = QLabel("Lines: 0")
        status_layout.addWidget(self.line_count_label)
        
        layout.addLayout(status_layout)
    
    def add_log_message(self, level: str, message: str):
        """Add a log message to the viewer with proper formatting."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check if this level should be shown
        current_filter = self.level_filter.currentText()
        if current_filter != "ALL" and level.upper() != current_filter:
            return
        
        # Limit number of lines by removing old ones if necessary
        document = self.log_text.document()
        if document.blockCount() >= self.max_lines:
            # Remove the first line
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove the newline
        
        # Move cursor to end
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Get colors based on current theme
        timestamp_color, level_color, message_color = self._get_log_colors(level)
        
        # Insert timestamp with muted color
        timestamp_format = QTextCharFormat()
        timestamp_format.setForeground(timestamp_color)
        cursor.setCharFormat(timestamp_format)
        cursor.insertText(f"{timestamp} - ")
        
        # Insert level with bold and colored text
        level_format = QTextCharFormat()
        level_format.setForeground(level_color)
        level_format.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(level_format)
        cursor.insertText(level.upper())
        
        # Insert separator and message with normal formatting
        separator_format = QTextCharFormat()
        separator_format.setForeground(message_color)
        cursor.setCharFormat(separator_format)
        cursor.insertText(f" - {message}\n")
        
        # Auto-scroll if enabled
        if self.auto_scroll:
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Update line count
        self.update_line_count()
    
    def _get_log_colors(self, level: str) -> tuple[QColor, QColor, QColor]:
        """Get timestamp, level, and message colors based on theme and log level.
        
        Returns:
            tuple: (timestamp_color, level_color, message_color)
        """
        level = level.upper()
        
        if self._is_dark_mode:
            # Dark mode colors
            timestamp_color = QColor(150, 150, 150)  # Muted gray for timestamp
            message_color = QColor(220, 220, 220)    # Light gray for message text
            
            level_colors = {
                'DEBUG': QColor(100, 150, 255),      # Light blue
                'INFO': QColor(80, 200, 120),        # Nice green
                'WARNING': QColor(255, 180, 50),     # Amber/orange
                'ERROR': QColor(255, 120, 120),      # Soft red
                'CRITICAL': QColor(200, 120, 255),   # Purple
            }
        else:
            # Light mode colors
            timestamp_color = QColor(120, 120, 120)  # Muted gray for timestamp
            message_color = QColor(50, 50, 50)       # Dark gray for message text
            
            level_colors = {
                'DEBUG': QColor(50, 100, 200),       # Medium blue
                'INFO': QColor(50, 150, 80),         # Forest green
                'WARNING': QColor(200, 140, 30),     # Amber/orange
                'ERROR': QColor(200, 50, 50),        # Dark red
                'CRITICAL': QColor(140, 50, 180),    # Purple
            }
        
        level_color = level_colors.get(level, message_color)
        return timestamp_color, level_color, message_color
    
    def get_level_color(self, level: str) -> QColor:
        """Get color for log level (legacy method for compatibility)."""
        _, level_color, _ = self._get_log_colors(level)
        return level_color
    
    def refresh_theme(self):
        """Refresh theme detection and update display."""
        self._is_dark_mode = self._detect_dark_mode()
        # Note: Existing log messages won't change color until new ones are added
        # For full refresh, we'd need to store messages and re-render them
    
    def filter_logs(self):
        """Filter logs based on selected level."""
        # For now, this just affects new messages
        # Full filtering would require storing all messages and re-displaying
        self.status_label.setText(f"Filter: {self.level_filter.currentText()}")
    
    def toggle_auto_scroll(self, enabled: bool):
        """Toggle auto-scroll functionality."""
        self.auto_scroll = enabled
        self.status_label.setText("Auto-scroll enabled" if enabled else "Auto-scroll disabled")
        
        # Auto-scroll timer to reset status message
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def clear(self):
        """Clear all log messages."""
        self.log_text.clear()
        self.update_line_count()
        self.status_label.setText("Logs cleared")
        
        # Auto-clear timer to reset status message
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))
    
    def update_line_count(self):
        """Update the line count display."""
        line_count = self.log_text.document().blockCount() - 1  # -1 because of extra empty line
        self.line_count_label.setText(f"Lines: {line_count}")
    
    def export_logs(self):
        """Export logs to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Logs",
                f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                
                QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{filename}")
                self.logger.info(f"Logs exported to: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export logs:\n{str(e)}")
            self.logger.error(f"Failed to export logs: {e}")
    
    def get_log_content(self) -> str:
        """Get current log content as plain text."""
        return self.log_text.toPlainText()
