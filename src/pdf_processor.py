import pymupdf  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.pdf_path = None
        self.doc = None

    def load(self, pdf_path: str) -> bool:
        """Load a PDF file"""
        try:
            self.pdf_path = pdf_path
            self.doc = pymupdf.open(self.pdf_path)
            logger.info(f"Loaded PDF: {self.pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF {pdf_path}: {e}")
            return False

    def extract_text(self) -> str | None:
        """Extract text from the loaded PDF"""
        if not self.doc:
            logger.error("No PDF loaded - call load() first")
            return None
            
        try:
            text = ""
            for page_num, page in enumerate(self.doc):
                page_text = page.get_text()
                text += page_text + "\n"
                logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            
            logger.info(f"Extracted {len(text)} total characters from PDF: {self.pdf_path}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return None

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            logger.debug(f"Closed PDF: {self.pdf_path}")
            self.doc = None
            self.pdf_path = None
