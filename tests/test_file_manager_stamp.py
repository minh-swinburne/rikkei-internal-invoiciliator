"""
Test script for the updated file_manager.py stamp_pdf method.
"""

import sys
from pathlib import Path

# Add src to path so we can import the modules
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.core.services.file_manager import FileManager
import pymupdf


def create_test_pdf() -> str:
    """Create a test PDF for stamping."""
    doc = pymupdf.open()
    page = doc.new_page()
    
    text = """INVOICE RECONCILIATION TEST
    
This is a test document to verify the improved PDF stamping functionality.
The stamp should be responsive, well-styled, and positioned correctly.

Invoice Number: INV-2025-001
PO Number: PO-2025-001
Amount: $1,234.56"""
    
    page.insert_text((50, 100), text, fontsize=11)
    
    test_path = "test_invoice.pdf"
    doc.save(test_path)
    doc.close()
    
    return test_path


def test_file_manager_stamping():
    """Test the improved stamping functionality."""
    print("Testing improved FileManager.stamp_pdf method...")
    
    # Create test PDF
    test_pdf = create_test_pdf()
    print(f"Created test PDF: {test_pdf}")
    
    # Initialize FileManager
    output_dir = Path("data/output/test_filemanager")
    file_manager = FileManager(output_dir)
    
    # Test different scenarios
    test_cases = [
        {
            "status": "APPROVED",
            "pic_name": "Luca Nguyen",
            "description": "Normal approval"
        },
        {
            "status": "REQUIRES REVIEW", 
            "pic_name": "Dr. Jane Elizabeth Smith-Johnson",
            "description": "Long name review"
        },
        {
            "status": "APPROVED",
            "pic_name": "Jo",
            "description": "Short name approval"
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\nTest {i+1}: {case['description']}")
        
        try:
            result_path = file_manager.stamp_pdf(
                test_pdf,
                case["status"],
                case["pic_name"]
            )
            print(f"✓ Success: {result_path}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\nTest completed! Check the output directory: {output_dir}")
    print("Files should show responsive sizing based on content length.")


if __name__ == "__main__":
    test_file_manager_stamping()
