"""
PDF viewer widget for displaying PDF documents in the GUI.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QSlider, QComboBox, QFrame
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QPixmap, QPainter, QImage

from ..logging_config import get_module_logger

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFRenderWorker(QObject):
    """Worker thread for rendering PDF pages."""
    
    page_rendered = Signal(int, QPixmap)
    error_occurred = Signal(str)
    
    def __init__(self, pdf_path: Path, page_num: int, zoom: float = 1.0):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_num = page_num
        self.zoom = zoom
    
    def render_page(self):
        """Render a PDF page to pixmap."""
        try:
            if not PYMUPDF_AVAILABLE:
                self.error_occurred.emit("PyMuPDF not available")
                return
            
            doc = fitz.open(str(self.pdf_path))
            if self.page_num >= len(doc):
                self.error_occurred.emit(f"Page {self.page_num} out of range")
                return
            
            page = doc[self.page_num]
            
            # Create transformation matrix for zoom
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimg = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(qimg)
            
            self.page_rendered.emit(self.page_num, pixmap)
            doc.close()
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to render page: {str(e)}")


class PDFViewer(QWidget):
    """PDF viewer widget with zoom and navigation controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.pdf_viewer')
        
        # State
        self.pdf_path: Optional[Path] = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.doc: Optional[object] = None  # PyMuPDF document
        
        # Worker thread
        self.render_thread: Optional[QThread] = None
        self.render_worker: Optional[PDFRenderWorker] = None
        
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
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setMaximumWidth(30)
        self.prev_btn.clicked.connect(self.previous_page)
        control_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("No PDF loaded")
        control_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setMaximumWidth(30)
        self.next_btn.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_btn)
        
        control_layout.addStretch()
        
        # Zoom controls
        control_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "Fit Width"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        control_layout.addWidget(self.zoom_combo)
        
        layout.addWidget(control_frame)
        
        # PDF display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setFrameStyle(QFrame.Shape.StyledPanel)
        
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_label.setMinimumSize(400, 300)
        self.pdf_label.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.show_message("No PDF loaded")
        
        self.scroll_area.setWidget(self.pdf_label)
        layout.addWidget(self.scroll_area)
        
        # Enable/disable controls based on availability
        self.update_controls()
    
    def show_message(self, message: str):
        """Show a message in the PDF display area."""
        self.pdf_label.setText(message)
        self.pdf_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0; color: #666;")
    
    def load_pdf(self, pdf_path: Path):
        """Load a PDF file for viewing."""
        try:
            self.pdf_path = pdf_path
            
            if not PYMUPDF_AVAILABLE:
                self.show_message("PDF viewing requires PyMuPDF\nPlease install: pip install PyMuPDF")
                return
            
            if not pdf_path.exists():
                self.show_message(f"PDF file not found:\n{pdf_path.name}")
                return
            
            # Open PDF document
            self.doc = fitz.open(str(pdf_path))
            self.total_pages = len(self.doc)
            self.current_page = 0
            
            # Load first page
            self.render_current_page()
            self.update_controls()
            
            self.logger.info(f"Loaded PDF: {pdf_path.name} ({self.total_pages} pages)")
            
        except Exception as e:
            self.logger.error(f"Failed to load PDF {pdf_path}: {e}")
            self.show_message(f"Error loading PDF:\n{str(e)}")
    
    def render_current_page(self):
        """Render the current page."""
        if not self.doc or not PYMUPDF_AVAILABLE:
            return
        
        try:
            # Stop any existing rendering
            if self.render_thread and self.render_thread.isRunning():
                self.render_thread.quit()
                self.render_thread.wait()
            
            # Show loading message
            self.show_message("Loading page...")
            
            # Start rendering in background thread
            self.render_thread = QThread()
            self.render_worker = PDFRenderWorker(self.pdf_path, self.current_page, self.zoom_level)
            self.render_worker.moveToThread(self.render_thread)
            
            # Connect signals
            self.render_worker.page_rendered.connect(self.on_page_rendered)
            self.render_worker.error_occurred.connect(self.on_render_error)
            self.render_thread.started.connect(self.render_worker.render_page)
            self.render_thread.finished.connect(self.render_thread.deleteLater)
            
            # Start rendering
            self.render_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to render page: {e}")
            self.show_message(f"Error rendering page:\n{str(e)}")
    
    def on_page_rendered(self, page_num: int, pixmap: QPixmap):
        """Handle page rendered signal."""
        if page_num == self.current_page:
            self.pdf_label.setPixmap(pixmap)
            self.pdf_label.setStyleSheet("border: 1px solid gray; background-color: white;")
            self.update_page_label()
    
    def on_render_error(self, error_message: str):
        """Handle render error signal."""
        self.show_message(f"Render Error:\n{error_message}")
        self.logger.error(f"PDF render error: {error_message}")
    
    def update_controls(self):
        """Update control states."""
        has_pdf = self.doc is not None and PYMUPDF_AVAILABLE
        
        self.prev_btn.setEnabled(has_pdf and self.current_page > 0)
        self.next_btn.setEnabled(has_pdf and self.current_page < self.total_pages - 1)
        self.zoom_combo.setEnabled(has_pdf)
        
        self.update_page_label()
    
    def update_page_label(self):
        """Update the page label."""
        if self.doc:
            self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        else:
            self.page_label.setText("No PDF loaded")
    
    def previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.render_current_page()
            self.update_controls()
    
    def next_page(self):
        """Go to next page."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_current_page()
            self.update_controls()
    
    def on_zoom_changed(self, zoom_text: str):
        """Handle zoom level change."""
        try:
            if zoom_text == "Fit Width":
                # Calculate zoom to fit width
                if self.doc and self.scroll_area.width() > 0:
                    page = self.doc[self.current_page]
                    page_width = page.rect.width
                    available_width = self.scroll_area.width() - 20  # Account for scrollbars
                    self.zoom_level = available_width / page_width
                else:
                    self.zoom_level = 1.0
            else:
                # Parse percentage
                zoom_percent = int(zoom_text.replace('%', ''))
                self.zoom_level = zoom_percent / 100.0
            
            # Re-render current page with new zoom
            if self.doc:
                self.render_current_page()
                
        except Exception as e:
            self.logger.error(f"Failed to change zoom: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events for fit-width zoom."""
        super().resizeEvent(event)
        if self.zoom_combo.currentText() == "Fit Width":
            self.on_zoom_changed("Fit Width")
    
    def closeEvent(self, event):
        """Clean up when widget is closed."""
        if self.render_thread and self.render_thread.isRunning():
            self.render_thread.quit()
            self.render_thread.wait()
        
        if self.doc:
            self.doc.close()
        
        super().closeEvent(event)
