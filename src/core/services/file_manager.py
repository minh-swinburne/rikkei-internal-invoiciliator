"""
File management for the invoice reconciliation tool.
Handles PDF stamping and file organization.
"""

import json
import shutil
from typing import Optional, Union, TYPE_CHECKING
from pathlib import Path
from datetime import datetime

import pymupdf  # PyMuPDF
from pymupdf import Rect

from ..models import Invoice, PurchaseOrder, ValidationResult
from ...settings import settings
from ...logging_config import get_module_logger

if TYPE_CHECKING:
    from ..workflow import ProcessingResult


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


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
    
    def process_pdf(self, pdf_path: str | Path, status: str) -> Path:
        """
        Process PDF: either stamp and save, or just copy to appropriate directory.
        
        Args:
            pdf_path: Path to the original PDF file
            status: Processing status ("APPROVED" or "REQUIRES REVIEW")
            
        Returns:
            Path to the processed file in the output directory
        """
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)
        
        if settings.enable_stamping:
            return self._stamp_and_save_pdf(pdf_path, status)
        else:
            return self._copy_pdf_to_directory(pdf_path, status)
    
    def _stamp_and_save_pdf(self, pdf_path: Path, status: str) -> Path:
        """
        Stamp PDF with approval status and save to appropriate directory.
        
        Args:
            pdf_path: Path to the original PDF file
            status: Status to stamp ("APPROVED" or "REQUIRES REVIEW")
            
        Returns:
            Path to the stamped file in the output directory
        """
        target_dir = self.approved_dir if status == "APPROVED" else self.review_dir
        target_path = target_dir / pdf_path.name
        
        self.logger.info(f"Stamping PDF: {pdf_path.name} with status: {status}")
        
        try:
            # Open the PDF
            doc = pymupdf.open(str(pdf_path))
            
            # Add stamp to first page
            page = doc[0]
            rect = page.rect
            pic_name = settings.stamp_pic_name
            
            # Calculate responsive dimensions based on content
            status_width = len(status) * 8.5  # Approximate width for status text (14px font)
            person_width = len(f"By {pic_name}") * 7  # Approximate width for person line (12px font)
            time_text = f"at {datetime.now().strftime('%I:%M %p, %b %d, %Y')}"
            time_width = len(time_text) * 7  # Approximate width for time line (12px font)
            
            # Find the longest line and add padding
            content_width = max(status_width, person_width, time_width)
            padding_x = 10  # 10px padding on each side
            padding_y = 6   # 6px padding on top and bottom
            border_width = 2  # 2px border on each side
            
            # Calculate responsive height based on content
            status_height = 20  # Base height for status line (16px font + spacing)
            person_height = 15  # Height for person line (12px font + spacing)
            time_height = 15    # Height for time line (12px font + spacing)
            
            content_height = status_height + person_height + time_height
            
            # Calculate final dimensions with min/max constraints
            width = min(max(content_width + padding_x * 2 + border_width * 2, 180), 320)
            height = min(max(content_height + padding_y * 2 + border_width * 2, 70), 110)
            
            # Position stamp based on settings
            margin_x = 20
            margin_y = 20
            tb, lr = settings.stamp_position.split("-")

            if tb == "top":
                y0 = margin_y
                y1 = margin_y + height
            else:  # bottom
                y0 = rect.height - height - margin_y
                y1 = rect.height - margin_y
            
            if lr == "left":
                x0 = margin_x
                x1 = margin_x + width
            else:  # right
                x0 = rect.width - width - margin_x
                x1 = rect.width - margin_x

            stamp_rect = Rect(x0, y0, x1, y1)
            
            # Create content rectangle with padding
            content_rect = Rect(
                x0 + padding_x,
                y0 + padding_y, 
                x1 - padding_x,
                y1 - padding_y
            )

            # Set stamp color based on status
            color = "#416a1c" if status == "APPROVED" else "#dc3545"  # Green for approved, red for review
            color_rgb = tuple(num / 255 for num in hex_to_rgb(color))
            
            # Draw the rounded rectangle background
            page.draw_rect(
                stamp_rect, 
                radius=(12 / stamp_rect.width, 12 / stamp_rect.height), 
                color=color_rgb, 
                fill=color_rgb, 
                fill_opacity=0.15,
                width=2
            )
            
            # Create HTML content with improved styling
            now = datetime.now()
            icon = "✓" if status == "APPROVED" else "⚠"
            formatted_time = now.strftime("%I:%M %p, %b %d, %Y").replace(" 0", " ")  # Remove leading zero
            
            html_content = f"""
            <div class="stamp">
                <div class="stamp-header">
                    <span class="stamp-icon">{icon}</span>
                    <span class="stamp-status">{status}</span>
                </div>
                <div class="stamp-footer">
                    <div class="person-line">By {pic_name}</div>
                    <div class="time-line">at {formatted_time}</div>
                </div>
            </div>
            """
            
            css = f"""
            .stamp {{
                height: 100%;
                width: 100%;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: flex-start;
            }}
            
            .stamp-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                width: 100%;
                line-height: 1.25;
            }}
            
            .stamp-icon {{
                color: {color};
                font-size: 16px;
                font-weight: bold;
                text-shadow: 1px 1px 1px rgba(255,255,255,0.6);
            }}
            
            .stamp-status {{
                color: {color};
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                flex-grow: 1;
                text-shadow: 1px 1px 1px rgba(255,255,255,0.6);
                letter-spacing: 0.5px;
            }}
            
            .stamp-footer {{
                color: {color};
                font-family: Arial, sans-serif;
                font-size: 12px;
                font-style: italic;
                line-height: 1.25;
                width: 100%;
            }}
            
            .person-line {{
                font-weight: 600;
                margin-bottom: 2px;
                text-shadow: 1px 1px 1px rgba(255,255,255,0.5);
            }}
            
            .time-line {{
                opacity: 0.85;
                text-shadow: 1px 1px 1px rgba(255,255,255,0.5);
            }}
            """

            # Add the stamp using the content rectangle (with padding)
            page.insert_htmlbox(
                content_rect,
                html_content,
                css=css
            )
            
            # Save stamped PDF
            doc.save(str(target_path))
            doc.close()
            
            self.logger.info(f"Successfully stamped and saved: {target_path}")
            return target_path
            
        except Exception as e:
            self.logger.error(f"Failed to stamp PDF {pdf_path.name}: {str(e)}")
            # Fallback: copy without stamping
            return self._copy_pdf_to_directory(pdf_path, status)
    
    def _copy_pdf_to_directory(self, pdf_path: Path, status: str) -> Path:
        """
        Copy PDF to appropriate directory without stamping.
        
        Args:
            pdf_path: Path to the original PDF file
            status: Processing status to determine target directory
            
        Returns:
            Path to the copied file
        """
        target_dir = self.approved_dir if status == "APPROVED" else self.review_dir
        target_path = target_dir / pdf_path.name
        
        shutil.copy2(str(pdf_path), str(target_path))
        self.logger.info(f"Copied PDF to: {target_path}")
        return target_path

    def save_result(
        self, 
        processing_result: 'ProcessingResult'
    ) -> Path:
        """Save the complete processing result to a file."""
        pdf_path = processing_result.pdf_path
        output_path = self.output_dir / "result" / f"{pdf_path.stem}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        processing_result.result_json_path = output_path

        with open(output_path, "w") as f:
            # Use Pydantic's model_dump_json for consistent serialization
            json_content = processing_result.model_dump_json(indent=4)
            f.write(json_content)
            
        self.logger.info(f"Processing result saved to: {output_path}")
        return output_path