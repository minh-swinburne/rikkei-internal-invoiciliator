"""
Log viewer widget for the invoice reconciliation GUI application.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QCheckBox, QComboBox, QLabel, QGroupBox, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QFont, QColor

from ..logging_config import get_module_logger


class LogViewer(QGroupBox):
    """Log viewer widget with filtering and export capabilities."""
    
    def __init__(self, parent=None):
        super().__init__("Processing Logs", parent)
        self.logger = get_module_logger('gui.log_viewer')
        
        # Settings
        self.max_lines = 1000
        self.auto_scroll = True
        
        self.setup_ui()
    
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
        """Add a log message to the viewer."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format the log line
        log_line = f"{timestamp} - {level.upper()} - {message}"
        
        # Apply color based on level
        color = self.get_level_color(level)
        
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
        
        # Add to text widget
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Set color for this line
        format = cursor.charFormat()
        format.setForeground(color)
        cursor.setCharFormat(format)
        
        cursor.insertText(log_line + "\n")
        
        # Auto-scroll if enabled
        if self.auto_scroll:
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Update line count
        self.update_line_count()
    
    def get_level_color(self, level: str) -> QColor:
        """Get color for log level."""
        level = level.upper()
        colors = {
            'DEBUG': QColor(128, 128, 128),    # Gray
            'INFO': QColor(0, 0, 0),           # Black
            'WARNING': QColor(255, 165, 0),    # Orange
            'ERROR': QColor(255, 0, 0),        # Red
            'CRITICAL': QColor(139, 0, 0),     # Dark red
        }
        return colors.get(level, QColor(0, 0, 0))
    
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
