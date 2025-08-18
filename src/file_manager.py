"""
File management for the invoice reconciliation tool.
Handles PDF stamping and file organization.
"""

import shutil
from pathlib import Path
from datetime import datetime

import pymupdf  # PyMuPDF
from pymupdf import Rect

from .settings import settings
from .logging_config import get_module_logger


class FileManager:
    """Handles file operations for processed invoices."""
    
    def __init__(self, output_dir: Path = Path("data/output")):
        """Initialize file manager with output directory."""
        self.logger = get_module_logger('file_manager')
        self.output_dir = output_dir
        self.approved_dir = self.output_dir / "approved"
        self.review_dir = self.output_dir / "review"
        
        # Create directories
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"FileManager initialized with output directory: {self.output_dir}")
    
    def stamp_pdf(self, pdf_path: str, status: str, pic_name: str) -> Path:
        """
        Stamp PDF with approval status and move to appropriate directory.
        
        Args:
            pdf_path: Path to the original PDF file
            status: Status to stamp ("APPROVED" or "REQUIRES REVIEW")
            
        Returns:
            Path to the stamped file in the output directory
        """
        if not settings.enable_stamping:
            self.logger.info("PDF stamping disabled in settings")
            return self._copy_without_stamping(pdf_path, status)
        
        source_path = Path(pdf_path)
        target_dir = self.approved_dir if status == "APPROVED" else self.review_dir
        target_path = target_dir / source_path.name
        
        self.logger.info(f"Stamping PDF: {source_path.name} with status: {status}")
        
        try:
            # Open the PDF
            doc = pymupdf.open(pdf_path)
            
            # Add stamp to first page
            page = doc[0]
            rect = page.rect
            width = 200
            height = 50
            
            # Position stamp based on settings
            if settings.stamp_position == "top-right":
                stamp_rect = Rect(rect.width - width - 20, 20, rect.width - 20, height + 20)
            elif settings.stamp_position == "top-left":
                stamp_rect = Rect(20, 20, width, height)
            elif settings.stamp_position == "bottom-left":
                stamp_rect = Rect(20, rect.height - height, width, rect.height - 20)
            else:  # bottom-right (default)
                stamp_rect = Rect(rect.width - width - 20, rect.height - height - 20, rect.width - 20, rect.height - 20)

            # Set stamp color based on status
            color = "#416a1c" if status == "APPROVED" else "#ff0000"  # Green for approved, red for review
            bg_color = "#e4eedd" if status == "APPROVED" else "#f8d7da"  # Light background
            today = datetime.today().date()
            label = f"<h3>{status}</h3><p>By {pic_name} on {today}</p>"
            css = f"""
body {{
    background-color: {bg_color};
    border: 2px solid {color};
    border-radius: 8px;
}}

* {{
    color: {color};
    font-family: system-ui;
    text-align: left;
}}

h3 {{
    font-size: 16px;
    margin-bottom: 10px;
}}

p {{
    font-size: 13px;
    font-style: italic;
    margin-bottom: 0;
}}
"""

            # Add the stamp
            page.insert_htmlbox(
                stamp_rect,
                label,
                css=css
            )
            
            # Save stamped PDF
            doc.save(str(target_path))
            doc.close()
            
            self.logger.info(f"Successfully stamped and saved: {target_path}")
            return target_path
            
        except Exception as e:
            self.logger.error(f"Failed to stamp PDF {source_path.name}: {str(e)}")
            # Fallback: copy without stamping
            return self._copy_without_stamping(pdf_path, status)
    
    def _copy_without_stamping(self, pdf_path: str, status: str) -> Path:
        """Copy PDF without stamping as fallback."""
        source_path = Path(pdf_path)
        target_dir = self.approved_dir if status == "APPROVED" else self.review_dir
        target_path = target_dir / source_path.name
        
        shutil.copy2(pdf_path, target_path)
        self.logger.info(f"Copied without stamping: {target_path}")
        return target_path
