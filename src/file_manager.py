"""
File management for the invoice reconciliation tool.
Handles PDF stamping and file organization.
"""

import shutil
from pathlib import Path

import fitz  # PyMuPDF

from .settings import settings
from .logging_config import get_module_logger


class FileManager:
    """Handles file operations for processed invoices."""
    
    def __init__(self, output_dir: str = "data/output"):
        """Initialize file manager with output directory."""
        self.logger = get_module_logger('file_manager')
        self.output_dir = Path(output_dir)
        self.approved_dir = self.output_dir / "approved"
        self.review_dir = self.output_dir / "review"
        
        # Create directories
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"FileManager initialized with output directory: {self.output_dir}")
    
    def stamp_pdf(self, pdf_path: str, status: str) -> Path:
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
            doc = fitz.open(pdf_path)
            
            # Add stamp to first page
            page = doc[0]
            rect = page.rect
            
            # Position stamp based on settings
            if settings.stamp_position == "top-right":
                stamp_rect = fitz.Rect(rect.width - 150, 20, rect.width - 20, 60)
            elif settings.stamp_position == "top-left":
                stamp_rect = fitz.Rect(20, 20, 150, 60)
            elif settings.stamp_position == "bottom-left":
                stamp_rect = fitz.Rect(20, rect.height - 60, 150, rect.height - 20)
            else:  # bottom-right (default)
                stamp_rect = fitz.Rect(rect.width - 150, rect.height - 60, rect.width - 20, rect.height - 20)
            
            # Set stamp color based on status
            color = (0, 0.7, 0) if status == "APPROVED" else (0.8, 0, 0)  # Green for approved, red for review
            
            # Add the stamp
            page.insert_textbox(
                stamp_rect,
                status,
                fontsize=12,
                fontname="helv",
                color=color,
                fill=(1, 1, 1),  # White background
                border_width=2,
                align=1  # Center align
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
