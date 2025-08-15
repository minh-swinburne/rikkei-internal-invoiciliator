import os
import shutil
import logging
from datetime import datetime
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, approved_dir: str, review_dir: str):
        self.approved_dir = approved_dir
        self.review_dir = review_dir
        os.makedirs(approved_dir, exist_ok=True)
        os.makedirs(review_dir, exist_ok=True)

    def move_file(self, src: str, approved: bool, vendor: str | None = None) -> str:
        """Move file to appropriate directory with vendor prefix"""
        dest_dir = self.approved_dir if approved else self.review_dir
        original_filename = os.path.basename(src)
        
        # Add vendor prefix if provided
        if vendor:
            filename = f"{vendor.upper()}_{original_filename}"
        else:
            filename = original_filename
            
        dest = os.path.join(dest_dir, filename)
        shutil.move(src, dest)
        logger.info(f"Moved file {src} to {dest}")
        return dest

    def stamp_pdf(self, pdf_path: str, stamp_text: str, pic_name: str = "AUTO-SYSTEM", date: str | None = None):
        """Stamp PDF with approval/review information"""
        date_str = date or datetime.now().strftime('%Y-%m-%d %H:%M')
        doc = fitz.open(pdf_path)
        
        # Stamp on the last page
        page = doc[-1]
        text = f"{stamp_text}\nBy {pic_name}\n{date_str}"
        
        # Position stamp in top-right corner
        rect = page.rect
        stamp_x = rect.width - 150
        stamp_y = 50
        
        # Choose color based on stamp type
        if "APPROVED" in stamp_text.upper():
            color = (0, 0.7, 0)  # Green
        else:
            color = (0.8, 0.4, 0)  # Orange for manual review
            
        page.insert_text((stamp_x, stamp_y), text, fontsize=10, color=color)
        doc.save(pdf_path)
        doc.close()
        logger.info(f"Stamped PDF {pdf_path} with: {stamp_text}")

    def copy_file_for_processing(self, src: str, temp_dir: str, vendor: str | None = None) -> str:
        """Create a temporary copy for processing to avoid modifying the original"""
        os.makedirs(temp_dir, exist_ok=True)
        temp_filename = f"temp_{os.path.basename(src)}"
        temp_path = os.path.join(temp_dir, temp_filename)
        shutil.copy2(src, temp_path)
        return temp_path
