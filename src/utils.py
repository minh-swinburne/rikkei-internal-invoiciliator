"""

"""

import re
from logging import Logger
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
import pymupdf
import json

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
            base_path = get_project_root()
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
    """Get the project root directory with PyInstaller compatibility."""
    import sys
    
    # When running as PyInstaller bundle, use the executable directory
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and sets _MEIPASS to it
        # But we want the directory where the .exe is located
        exe_dir = Path(sys.executable).parent
        return exe_dir
    
    # For development/normal Python execution
    # Find the directory containing main.py or .git
    current = Path(__file__).parent.parent  # Go up from src/ to project root
    
    # Look for markers that indicate project root
    markers = ['main.py', '.git', 'requirements.txt', 'gui_launcher.py']
    
    for marker in markers:
        if (current / marker).exists():
            return current
    
    # Fallback to parent of src directory
    return current

def load_json(json_path: Path, logger: Optional[Logger] = None) -> Any:
    if json_path.exists():
        # Try different encodings to handle problematic files
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                with open(json_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                if logger:
                    logger.debug(f"Successfully loaded JSON with {encoding} encoding")
                return data
            except UnicodeDecodeError:
                if logger:
                    logger.debug(f"Failed to decode with {encoding}, trying next encoding")
                continue
            except json.JSONDecodeError as je:
                if logger:
                    logger.error(f"JSON decode error with {encoding}: {je}")
                # If JSON is malformed, we can't use any encoding to fix it
                break
    return None

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


def convert_markdown_to_html(text: str) -> str:
    """
    Convert basic markdown elements to HTML.
    
    This function handles common markdown formatting like bold, italic, code,
    links, and horizontal rules. Used as a fallback when native markdown
    rendering is not available.
    
    Args:
        text: Markdown text to convert
        
    Returns:
        HTML formatted text
    """
    if not text:
        return ""
    
    # Bold text **text** or __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
    
    # Italic text *text* or _text_
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    
    # Code `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Remove markdown horizontal rules
    text = re.sub(r'^---+$', '<hr>', text, flags=re.MULTILINE)
    
    return text


def format_markdown_code_block(paragraph: str) -> str:
    """
    Format a markdown code block for HTML display.
    
    Args:
        paragraph: Paragraph containing code block
        
    Returns:
        Formatted HTML code block
    """
    lines = paragraph.split('\n')
    code_lines = []
    
    for line in lines:
        if not line.strip().startswith('```'):
            code_lines.append(line)
    
    code_content = '\n'.join(code_lines)
    return f'<pre><code>{code_content}</code></pre>'


def is_markdown_list_paragraph(paragraph: str) -> bool:
    """
    Check if a paragraph contains a markdown list.
    
    Args:
        paragraph: Text paragraph to check
        
    Returns:
        True if paragraph contains list items
    """
    lines = paragraph.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # Check if most lines start with numbers or dashes
    list_lines = 0
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '•', '*')) or
            re.match(r'^\d+\.', stripped)):
            list_lines += 1
    
    return list_lines >= len(lines) * 0.6  # At least 60% of lines are list items


def format_markdown_list_to_html(paragraph: str) -> str:
    """
    Convert a markdown list paragraph to HTML.
    
    Args:
        paragraph: Paragraph containing list items
        
    Returns:
        HTML formatted list
    """
    lines = paragraph.strip().split('\n')
    list_items = []
    
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Remove common list prefixes
            for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '•', '*']:
                if stripped.startswith(prefix):
                    stripped = stripped[len(prefix):].strip()
                    break
            
            # Also handle numbered lists
            stripped = re.sub(r'^\d+\.\s*', '', stripped)
            
            if stripped:
                list_items.append(f"<li>{stripped}</li>")
    
    if list_items:
        return f"<ul>{''.join(list_items)}</ul>"
    else:
        return f"<p>{paragraph}</p>"