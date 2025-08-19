"""
Test script for the refactored main workflow.
Tests the new architecture with global services and Path objects.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import initialize_services, process_single_pdf
import pymupdf
from src.settings import settings


def create_test_pdf() -> Path:
    """Create a test PDF for processing."""
    doc = pymupdf.open()
    page = doc.new_page()
    
    text = """INVOICE RECONCILIATION TEST
    
This is a test document for the refactored workflow.
    
Invoice Number: INV-2025-001
PO Number: PO-2025-001
Amount: $1,234.56

The refactored architecture includes:
• Global service instances (no recreation per PDF)
• Path objects throughout the pipeline
• Decoupled stamping and file copying
• Better error handling and logging"""
    
    page.insert_text((50, 100), text, fontsize=11)
    
    test_path = Path("test_refactored_workflow.pdf")
    doc.save(str(test_path))
    doc.close()
    
    return test_path


def test_refactored_workflow():
    """Test the refactored workflow."""
    print("Testing refactored workflow...")
    
    # Create test PDF
    test_pdf = create_test_pdf()
    print(f"Created test PDF: {test_pdf}")
    
    # Set up test environment
    output_dir = Path("data/output/test_refactored")
    
    # Configure settings for testing
    settings.enable_stamping = True
    settings.stamp_pic_name = "Test User"
    settings.stamp_position = "top-right"
    
    try:
        # Initialize global services (this replaces per-PDF initialization)
        print("Initializing global services...")
        initialize_services(output_dir)
        print("✓ Services initialized successfully")
        
        # Process the PDF using refactored workflow
        print("Processing PDF with refactored workflow...")
        success = process_single_pdf(test_pdf)
        
        if success:
            print("✓ PDF processed successfully with refactored workflow")
            print(f"Check output directory: {output_dir}")
        else:
            print("✗ PDF processing failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        if test_pdf.exists():
            test_pdf.unlink()
            print(f"Cleaned up test file: {test_pdf}")


if __name__ == "__main__":
    test_refactored_workflow()
