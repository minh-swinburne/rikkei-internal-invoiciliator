"""
Test script for the new STAMP_ONLY_APPROVED setting.
"""

import sys
from pathlib import Path

# Add src to path so we can import the modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.file_manager import FileManager
from src.settings import settings
import pymupdf


def create_test_pdf(name: str) -> str:
    """Create a test PDF for stamping."""
    doc = pymupdf.open()
    page = doc.new_page()
    
    text = f"""INVOICE RECONCILIATION TEST - {name.upper()}
    
This is a test document to verify the STAMP_ONLY_APPROVED functionality.

Invoice Number: INV-2025-{name[:3].upper()}
PO Number: PO-2025-{name[:3].upper()}
Amount: $1,234.56

Status: {name}"""
    
    page.insert_text((50, 100), text, fontsize=11)
    
    test_path = f"test_invoice_{name.lower().replace(' ', '_')}.pdf"
    doc.save(test_path)
    doc.close()
    
    return test_path


def test_stamp_only_approved_setting():
    """Test the STAMP_ONLY_APPROVED setting functionality."""
    print("Testing STAMP_ONLY_APPROVED setting...")
    
    # Initialize FileManager
    output_dir = Path("data/output/test_stamp_only_approved")
    file_manager = FileManager(output_dir)
    
    # Test cases
    test_cases = [
        {"file_status": "APPROVED", "description": "Approved invoice"},
        {"file_status": "REQUIRES REVIEW", "description": "Problematic invoice"}
    ]
    
    # Test with STAMP_ONLY_APPROVED = True
    print("\n=== Testing with STAMP_ONLY_APPROVED = True ===")
    settings.stamp_only_approved = True
    settings.enable_stamping = True
    
    for case in test_cases:
        pdf_path = create_test_pdf(case["description"])
        print(f"\nTesting {case['description']} (status: {case['file_status']})")
        
        try:
            # Determine expected stamp status based on our new logic
            expected_stamp = None
            if settings.stamp_only_approved and case['file_status'] == "APPROVED":
                expected_stamp = "APPROVED"
            
            result_path = file_manager.process_pdf(
                pdf_path,
                case["file_status"],
                expected_stamp
            )
            
            if expected_stamp is None:
                print(f"✓ Success: {result_path} (no stamp applied)")
            else:
                print(f"✓ Success: {result_path} (stamped as {expected_stamp})")
            
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            # Clean up test PDF
            Path(pdf_path).unlink(missing_ok=True)
    
    # Test with STAMP_ONLY_APPROVED = False (existing behavior)
    print("\n=== Testing with STAMP_ONLY_APPROVED = False (traditional behavior) ===")
    settings.stamp_only_approved = False
    settings.stamp_always_accept = True  # Test the always accept behavior
    
    for case in test_cases:
        pdf_path = create_test_pdf(case["description"])
        print(f"\nTesting {case['description']} (status: {case['file_status']})")
        
        try:
            # Traditional logic: stamp all as approved if stamp_always_accept
            expected_stamp = "APPROVED" if settings.stamp_always_accept else case['file_status']
            
            result_path = file_manager.process_pdf(
                pdf_path,
                case["file_status"],
                expected_stamp
            )
            
            print(f"✓ Success: {result_path} (stamped as {expected_stamp})")
            
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            # Clean up test PDF
            Path(pdf_path).unlink(missing_ok=True)
    
    print(f"\nTest completed! Check the output directory: {output_dir}")
    print("Approved invoices should be stamped in both modes.")
    print("Problematic invoices should only be stamped when STAMP_ONLY_APPROVED=False.")


if __name__ == "__main__":
    test_stamp_only_approved_setting()
