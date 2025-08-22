"""
Test script for PDF stamping with PyMuPDF.
Tests various styling approaches including div wrapping, gradients, and responsive sizing.
"""

import pymupdf
from pymupdf import Rect
from pathlib import Path
from datetime import datetime


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_test_pdf(output_dir: str) -> Path:
    """Create a simple test PDF for stamping experiments."""
    doc = pymupdf.open()  # Create new PDF
    page = doc.new_page()
    
    # Add some content to the page
    text = "This is a test PDF for stamp testing.\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit."
    page.insert_text((50, 100), text, fontsize=12)
    
    output_path = Path(output_dir) / "test_pdf.pdf"
    doc.save(str(output_path))
    doc.close()
    return output_path


def test_stamp_variations(pdf_path: str, output_dir: str):
    """Test different stamp variations for different statuses with responsive sizing."""
    print("Testing stamp variations with responsive sizing...")
    
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    rect = page.rect
    
    variations = [
        {
            "status": "APPROVED",
            "person": "Luca Nguyen",
            "time": "6:10 pm, Aug 18, 2025",
            "color": "#416a1c",
            "icon": "✓"
        },
        {
            "status": "REQUIRES REVIEW",
            "person": "Jane Smith",
            "time": "2:30 pm, Aug 19, 2025",
            "color": "#dc3545",
            "icon": "⚠"
        },
        {
            "status": "PENDING",
            "person": "Mike Johnson",
            "time": "9:15 am, Aug 19, 2025",
            "color": "#856404",
            "icon": "⏳"
        }
    ]
    
    for i, var in enumerate(variations):
        # Calculate responsive dimensions based on content
        status_width = len(var['status']) * 8  # Approximate width for status text
        person_width = len(f"By {var['person']}") * 6  # Approximate width for person line
        time_width = len(f"at {var['time']}") * 6  # Approximate width for time line
        
        # Find the longest line and add padding
        content_width = max(status_width, person_width, time_width)
        padding_x = 10  # 10px padding on each side
        padding_y = 6  # 6px padding on top and bottom
        border_width = 2  # 2px border on each side
        
        # Calculate responsive height based on content
        # Base height for status line (16px font + spacing)
        status_height = 20
        # Height for person line (12px font + spacing)
        person_height = 15
        # Height for time line (12px font + spacing)
        time_height = 15
        
        content_height = status_height + person_height + time_height
        
        # Calculate final dimensions with min/max constraints
        width = min(max(content_width + padding_x * 2 + border_width * 2, 180), 300)
        height = min(max(content_height + padding_y * 2 + border_width * 2, 60), 100)
        
        # Position each stamp
        offset = 20
        y_pos = 50 + i * (height + 20)  # 20px spacing between stamps
        x_pos = rect.width - width - offset
        
        # Create the rectangle for background
        stamp_rect = Rect(x_pos, y_pos, x_pos + width, y_pos + height)
        
        # Create a smaller rectangle for content (with padding)
        content_rect = Rect(
            x_pos + padding_x, 
            y_pos + padding_y, 
            x_pos + width - padding_x, 
            y_pos + height - padding_y
        )
        
        color = tuple(num / 255 for num in hex_to_rgb(var['color']))

        # Draw the rounded rectangle background
        page.draw_rect(
            stamp_rect, 
            radius=(10 / stamp_rect.width, 10 / stamp_rect.height), 
            color=color, 
            fill=color, 
            fill_opacity=0.2,
            width=2
        )

        html_content = f"""
        <div class="stamp">
            <div class="stamp-header">
                <span class="stamp-icon">{var['icon']}</span>
                <span class="stamp-status">{var['status']}</span>
            </div>
            <div class="stamp-footer">
                <span>By {var['person']}</span>
                <span>at {var['time']}</span>
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
            gap: 6px;
            width: 100%;
            line-height: 1.25;
        }}
        
        .stamp-icon {{
            color: {var['color']};
            font-size: 16px;
            font-weight: bold;
        }}
        
        .stamp-status {{
            color: {var['color']};
            font-family: Arial, sans-serif;
            font-size: 14px;
            font-weight: bold;
            flex-grow: 1;
        }}
        
        .stamp-footer {{
            color: {var['color']};
            font-family: Arial, sans-serif;
            font-style: italic;
            font-size: 12px;
            text-align: left;
            line-height: 1.25;
        }}
        """
        
        # Insert HTML content into the content rectangle (with padding)
        page.insert_htmlbox(content_rect, html_content, css=css)

    output_path = Path(output_dir) / "test_stamp_variations.pdf"
    doc.save(str(output_path))
    doc.close()
    print(f"Saved: {output_path}")
    return output_path


def main():
    """Run stamp test."""
    output_dir = "data/output/test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("Creating test PDF...")
    test_pdf = create_test_pdf(output_dir)
    
    print("\nRunning stamp test...")
    result_path = test_stamp_variations(test_pdf, output_dir)

    print(f"\nTest completed! Check the generated PDF file:")
    print(f"- {result_path}")


if __name__ == "__main__":
    main()

