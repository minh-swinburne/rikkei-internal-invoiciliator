"""
Native PySide6 PDF viewer widget using QPdfView and QPdfDocument.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QComboBox, QFrame, QSpinBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

from ..logging_config import get_module_logger


class NativePDFViewer(QWidget):
    """Native PDF viewer using PySide6's QPdfView and QPdfDocument."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.native_pdf_viewer')
        
        # State
        self.pdf_path: Optional[Path] = None
        self.pdf_document: Optional[QPdfDocument] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        
        # Page navigation
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        control_layout.addWidget(self.prev_btn)
        
        # Page number input
        control_layout.addWidget(QLabel("Page:"))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self.go_to_page)
        control_layout.addWidget(self.page_spinbox)
        
        self.page_count_label = QLabel("of 0")
        control_layout.addWidget(self.page_count_label)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addStretch()
        
        # Zoom controls
        control_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems([
            "Fit Width", "Fit Page", "50%", "75%", "100%", "125%", "150%", "200%", "300%"
        ])
        self.zoom_combo.setCurrentText("Fit Width")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        control_layout.addWidget(self.zoom_combo)
        
        # Zoom in/out buttons
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMaximumWidth(30)
        zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMaximumWidth(30)
        zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(zoom_out_btn)
        
        layout.addWidget(control_frame)
        
        # PDF view
        self.pdf_view = QPdfView()
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        
        # Create PDF document
        self.pdf_document = QPdfDocument()
        self.pdf_document.statusChanged.connect(self.on_document_status_changed)
        self.pdf_document.pageCountChanged.connect(self.on_page_count_changed)
        
        # Connect document to view
        self.pdf_view.setDocument(self.pdf_document)
        
        layout.addWidget(self.pdf_view)
        
        # Initialize controls
        self.update_controls()
    
    def show_message(self, message: str):
        """Show a message (for compatibility with PDFViewer interface)."""
        # For native PDF viewer, we can show status in the page label or use tooltip
        self.page_count_label.setText(message)
        self.page_count_label.setToolTip(message)
    
    def load_pdf(self, pdf_path: Path):
        """Load a PDF file for viewing."""
        try:
            self.pdf_path = pdf_path
            
            if not pdf_path.exists():
                QMessageBox.warning(self, "File Not Found", f"PDF file not found:\n{pdf_path.name}")
                return
            
            # Load the PDF document
            pdf_file_path = str(pdf_path.resolve())
            self.pdf_document.load(pdf_file_path)
            
            self.logger.info(f"Loading PDF: {pdf_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load PDF {pdf_path}: {e}")
            QMessageBox.critical(self, "Error", f"Error loading PDF:\n{str(e)}")
    
    def on_document_status_changed(self):
        """Handle document status changes."""
        status = self.pdf_document.status()
        
        if status == QPdfDocument.Status.Ready:
            self.logger.info(f"PDF loaded successfully: {self.pdf_document.pageCount()} pages")
            self.update_controls()
        elif status == QPdfDocument.Status.Error:
            error_msg = f"Error loading PDF: {self.pdf_document.error()}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "PDF Error", error_msg)
    
    def on_page_count_changed(self, page_count: int):
        """Handle page count changes."""
        self.page_spinbox.setMaximum(page_count)
        self.page_count_label.setText(f"of {page_count}")
        self.update_controls()
    
    def update_controls(self):
        """Update control states."""
        has_pdf = self.pdf_document.status() == QPdfDocument.Status.Ready
        page_count = self.pdf_document.pageCount() if has_pdf else 0
        current_page = self.page_spinbox.value()
        
        self.prev_btn.setEnabled(has_pdf and current_page > 1)
        self.next_btn.setEnabled(has_pdf and current_page < page_count)
        self.page_spinbox.setEnabled(has_pdf)
        self.zoom_combo.setEnabled(has_pdf)
    
    def previous_page(self):
        """Go to previous page."""
        current_page = self.page_spinbox.value()
        if current_page > 1:
            self.page_spinbox.setValue(current_page - 1)
    
    def next_page(self):
        """Go to next page."""
        current_page = self.page_spinbox.value()
        page_count = self.pdf_document.pageCount()
        if current_page < page_count:
            self.page_spinbox.setValue(current_page + 1)
    
    def go_to_page(self, page_number: int):
        """Go to a specific page."""
        # QPdfView uses 0-based indexing, spinbox uses 1-based
        self.pdf_view.pageNavigator().jump(page_number - 1, QUrl(), 1.0)
        self.update_controls()
    
    def on_zoom_changed(self, zoom_text: str):
        """Handle zoom level change."""
        try:
            if zoom_text == "Fit Width":
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            elif zoom_text == "Fit Page":
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            else:
                # Parse percentage
                zoom_percent = int(zoom_text.replace('%', ''))
                zoom_factor = zoom_percent / 100.0
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
                self.pdf_view.setZoomFactor(zoom_factor)
                
        except Exception as e:
            self.logger.error(f"Failed to change zoom: {e}")
    
    def zoom_in(self):
        """Zoom in by 25%."""
        current_zoom = self.pdf_view.zoomFactor()
        new_zoom = min(current_zoom * 1.25, 5.0)  # Max 500%
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(new_zoom)
        
        # Update combo box to show current zoom
        zoom_percent = int(new_zoom * 100)
        zoom_text = f"{zoom_percent}%"
        index = self.zoom_combo.findText(zoom_text)
        if index >= 0:
            self.zoom_combo.setCurrentIndex(index)
        else:
            self.zoom_combo.setEditText(zoom_text)
    
    def zoom_out(self):
        """Zoom out by 25%."""
        current_zoom = self.pdf_view.zoomFactor()
        new_zoom = max(current_zoom / 1.25, 0.1)  # Min 10%
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(new_zoom)
        
        # Update combo box to show current zoom
        zoom_percent = int(new_zoom * 100)
        zoom_text = f"{zoom_percent}%"
        index = self.zoom_combo.findText(zoom_text)
        if index >= 0:
            self.zoom_combo.setCurrentIndex(index)
        else:
            self.zoom_combo.setEditText(zoom_text)
