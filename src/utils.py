"""

"""

from pathlib import Path
from datetime import datetime
import pymupdf
import os

def get_timestamp():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return timestamp

def get_relative_path(absolute_path: str | Path, base_path: str | Path = None) -> str:
    """
    Convert absolute path to relative path for cleaner UI display.
    Always returns paths with forward slashes for consistent display.
    
    Args:
        absolute_path: The absolute path to convert
        base_path: Base path to calculate relative from (defaults to current working directory)
    
    Returns:
        Relative path as string with forward slashes, or original path if conversion fails
    """
    try:
        abs_path = Path(absolute_path).resolve()
        if base_path is None:
            base_path = Path.cwd()
        else:
            base_path = Path(base_path).resolve()
        
        # Try to get relative path
        relative_path = abs_path.relative_to(base_path)
        # Normalize to forward slashes for consistent UI display
        return str(relative_path).replace('\\', '/')
        
    except (ValueError, OSError):
        # If relative path cannot be calculated (e.g., different drives on Windows),
        # return the absolute path as fallback with forward slashes
        return str(absolute_path).replace('\\', '/')

def get_project_root() -> Path:
    """Get the project root directory."""
    # Find the directory containing main.py or .git
    current = Path(__file__).parent.parent  # Go up from src/ to project root
    
    # Look for markers that indicate project root
    markers = ['main.py', '.git', 'requirements.txt', 'gui_launcher.py']
    
    for marker in markers:
        if (current / marker).exists():
            return current
    
    # Fallback to parent of src directory
    return current

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_test_pdf(output_dir: str | Path = Path()) -> Path:
    """Create a simple test PDF for experiments."""
    doc = pymupdf.open()
    invoice_page = doc.new_page()
    po_page = doc.new_page()

    invoice_text = """INVOICE
    
This is a test invoice.
    
Invoice Number: INV-2025-001
PO Number: PO-2025-001
Vendor: ABC Corp

Items:
| SKU  | Item Description | Ordered | Shipped | Unit Price | Total Price |
|------|------------------|---------|---------|------------|-------------|
| W001 | Widget A         | 2       | 2       | $50.00     | $100.00     |
| W002 | Widget B         | 1       | 1       | $75.00     | $75.00      |
| W003 | Widget C         | 10      | 5       | $20.00     | $100.00     |
|      | **Total**        |         |         |            | **$275.00** |

Freight: $25.00
Total: $300.00
Signature: ______________________
"""
    po_text = """PURCHASE ORDER

This is a test purchase order.

PO#: PO-2025-001

Items:
| SKU  | Item Description | Quantity | Unit Price | Total Price |
|------|------------------|----------|------------|-------------|
| W001 | Widget A         | 2        | $50.00     | $100.00     |
| W002 | Widget B         | 1        | $75.00     | $75.00      |
| W003 | Widget C         | 10       | $20.00     | $200.00     |
|      | **Total**        |          |            | **$375.00** |

Order Total: $375.00
Signature: ______________________
"""
    
    invoice_page.insert_text((50, 100), invoice_text, fontsize=11)
    po_page.insert_text((50, 100), po_text, fontsize=11)

    output_path = Path(output_dir) / "test_pdf.pdf"
    doc.save(str(output_path))
    doc.close()
    
    return output_path


def normalize_path_display(path: str | Path) -> str:
    """
    Normalize path for consistent UI display using forward slashes.
    
    Args:
        path: Path to normalize
        
    Returns:
        Path string with forward slashes
    """
    return str(path).replace('\\', '/')