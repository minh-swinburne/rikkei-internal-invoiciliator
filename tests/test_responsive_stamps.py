"""
Enhanced test script for responsive PDF stamping.
Demonstrates how stamps adapt to different content lengths.
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
    text = """RESPONSIVE STAMP TESTING DOCUMENT
    
This document demonstrates responsive PDF stamping where both width and height
adapt to the content length. Each stamp will be sized differently based on:

• Length of status text
• Length of person name 
• Length of timestamp
• Overall content dimensions

The stamps maintain consistent padding and styling while adapting their size."""
    
    page.insert_text((50, 80), text, fontsize=11)
    
    output_path = Path(output_dir) / "responsive_test.pdf"
    doc.save(str(output_path))
    doc.close()
    return output_path


def create_responsive_stamp(page, x: float, y: float, status: str, person: str, timestamp: str, color: str, icon: str) -> tuple[float, float]:
    """
    Create a single responsive stamp and return its dimensions.
    
    Args:
        page: PyMuPDF page object
        x, y: Position coordinates
        status: Status text
        person: Person name
        timestamp: Timestamp text
        color: Hex color code
        icon: Icon character
        
    Returns:
        tuple: (width, height) of the created stamp
    """
    # Calculate responsive dimensions based on content
    icon_width = 20  # Space for icon
    status_width = len(status) * 8.5  # Approximate width for status text (14px font)
    person_width = len(f"By {person}") * 7  # Approximate width for person line (12px font)
    time_width = len(f"at {timestamp}") * 7  # Approximate width for time line (12px font)
    
    # Find the longest line and add padding
    content_width = max(icon_width + status_width, person_width, time_width)
    padding_x = 12  # 12px padding on each side
    padding_y = 10  # 10px padding on top and bottom
    border_width = 2  # 2px border on each side
    
    # Calculate responsive height based on content
    # Base height for status line (16px font + spacing)
    status_height = 22
    # Height for person line (12px font + spacing)
    person_height = 16
    # Height for time line (12px font + spacing)  
    time_height = 16
    # Gap between header and footer
    gap_height = 6
    
    content_height = status_height + person_height + time_height + gap_height
    
    # Calculate final dimensions with min/max constraints
    width = min(max(content_width + padding_x * 2 + border_width * 2, 160), 350)
    height = min(max(content_height + padding_y * 2 + border_width * 2, 70), 120)
    
    # Create the rectangle for background
    stamp_rect = Rect(x, y, x + width, y + height)
    
    # Create a smaller rectangle for content (with padding)
    content_rect = Rect(
        x + padding_x, 
        y + padding_y, 
        x + width - padding_x, 
        y + height - padding_y
    )
    
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

    html_content = f"""
    <div class="stamp">
        <div class="stamp-header">
            <span class="stamp-icon">{icon}</span>
            <span class="stamp-status">{status}</span>
        </div>
        <div class="stamp-footer">
            <div class="person-line">By {person}</div>
            <div class="time-line">at {timestamp}</div>
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
        margin-bottom: 6px;
        width: 100%;
    }}
    
    .stamp-icon {{
        color: {color};
        font-size: 18px;
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
        line-height: 1.4;
        width: 100%;
    }}
    
    .person-line {{
        font-weight: 600;
        margin-bottom: 2px;
        text-shadow: 1px 1px 1px rgba(255,255,255,0.5);
    }}
    
    .time-line {{
        font-style: italic;
        opacity: 0.85;
        text-shadow: 1px 1px 1px rgba(255,255,255,0.5);
    }}
    """
    
    # Insert HTML content into the content rectangle (with padding)
    page.insert_htmlbox(content_rect, html_content, css=css)
    
    return width, height


def test_responsive_variations():
    """Test stamps with various content lengths to demonstrate responsiveness."""
    output_dir = "data/output/test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("Creating responsive stamp test...")
    test_pdf = create_test_pdf(output_dir)
    
    doc = pymupdf.open(str(test_pdf))
    page = doc[0]
    rect = page.rect
    
    # Test cases with varying content lengths
    test_cases = [
        {
            "status": "OK",
            "person": "Jo",
            "timestamp": "3:00 PM, Aug 19",
            "color": "#416a1c",
            "icon": "✓"
        },
        {
            "status": "APPROVED",
            "person": "Luca Nguyen",
            "timestamp": "6:10 pm, Aug 18, 2025",
            "color": "#416a1c",
            "icon": "✓"
        },
        {
            "status": "REQUIRES DETAILED REVIEW",
            "person": "Dr. Jane Elizabeth Smith-Johnson",
            "timestamp": "11:45 PM, August 19th, 2025",
            "color": "#dc3545",
            "icon": "⚠"
        },
        {
            "status": "PENDING APPROVAL",
            "person": "Mike",
            "timestamp": "9:15 am, Aug 19, 2025",
            "color": "#856404",
            "icon": "⏳"
        },
        {
            "status": "CONDITIONALLY APPROVED WITH NOTES",
            "person": "Alexander von Habsburg-Lorraine III",
            "timestamp": "2:30:45 PM, Wednesday, August 19th, 2025",
            "color": "#0d6efd",
            "icon": "📝"
        }
    ]
    
    # Position stamps in a grid
    start_x = 50
    start_y = 200
    current_x = start_x
    current_y = start_y
    offset = 20
    max_width = rect.width - 100  # Leave some margin
    
    print("Creating stamps with responsive sizing...")
    
    for i, case in enumerate(test_cases):
        # Create the stamp and get its dimensions
        width, height = create_responsive_stamp(
            page, current_x, current_y,
            case["status"], case["person"], case["timestamp"],
            case["color"], case["icon"]
        )
        
        print(f"Stamp {i+1}: '{case['status'][:20]}...' -> {width:.1f}x{height:.1f}px")
        
        # Move to next position
        current_y += height + offset
        
        # If we're getting close to the bottom, wrap to next column
        if current_y + 100 > rect.height:
            current_x += 360  # Move to next column
            current_y = start_y
    
    output_path = Path(output_dir) / "responsive_stamps_test.pdf"
    doc.save(str(output_path))
    doc.close()
    
    print(f"\nTest completed! Saved: {output_path}")
    return output_path


def main():
    """Run the responsive stamp test."""
    result_path = test_responsive_variations()
    print(f"\nCheck the PDF to see how stamps adapt to different content lengths:")
    print(f"- {result_path}")


if __name__ == "__main__":
    main()
