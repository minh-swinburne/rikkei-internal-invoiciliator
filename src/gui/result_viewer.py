"""
Result viewer for detailed invoice processing results.

This will be implemented in Phase 4.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class ResultViewer(QDialog):
    """Result viewer dialog for detailed processing results."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Processing Result Details")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Placeholder content
        placeholder = QLabel("Result viewer will be implemented in Phase 4")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)
