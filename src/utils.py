"""

"""

from pathlib import Path
from datetime import datetime
import pymupdf

def get_timestamp():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return timestamp

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