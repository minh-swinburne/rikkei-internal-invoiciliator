"""
PDF processing for the invoice reconciliation tool.
"""

import pymupdf  # PyMuPDF

from .logging_config import get_module_logger


class PDFProcessor:
    """Handles PDF text extraction and processing."""
    
    def __init__(self):
        """Initialize the PDF processor."""
        self.logger = get_module_logger('pdf_processor')
        self.pdf_path = None
        self.doc = None

    def load(self, pdf_path: str) -> bool:
        """Load a PDF file"""
        try:
            self.pdf_path = pdf_path
            self.doc = pymupdf.open(self.pdf_path)
            self.logger.info(f"Loaded PDF: {self.pdf_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load PDF {pdf_path}: {e}")
            return False

    def extract_text(self, pdf_path: str = None) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file (optional if already loaded)
            
        Returns:
            Extracted text as a string
        """
        # If pdf_path is provided, load it first
        if pdf_path:
            if not self.load(pdf_path):
                return ""
        
        if not self.doc:
            self.logger.error("No PDF loaded - call load() first or provide pdf_path")
            return ""
            
        try:
            text = ""
            for page_num, page in enumerate(self.doc):
                page_text = page.get_text()
                text += f"## Page {page_num + 1}:\n{page_text}\n\n---\n\n"
                self.logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            
            self.logger.info(f"Extracted {len(text)} total characters from PDF: {self.pdf_path}")
            return text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            self.logger.debug(f"Closed PDF: {self.pdf_path}")
            self.doc = None
            self.pdf_path = None
