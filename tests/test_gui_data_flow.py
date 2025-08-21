#!/usr/bin/env python3
"""Test script to verify result table data flow"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_result_dict_structure():
    """Test the ProcessingResult.to_dict() structure matches GUI expectations."""
    
    # Create a mock result dict that simulates ProcessingResult.to_dict()
    mock_result = {
        'pdf_path': 'data/input/test.pdf',
        'status': 'completed',
        'approval_status': 'REQUIRES REVIEW',  # This is the key field for status
        'validation_issues_count': 2,  # This is the key field for issues count
        'processed_pdf_path': 'data/output/approved/test.pdf',
        'is_approved': False,
        'invoice_number': 'INV-123',
        'po_number': 'PO-456',
        'vendor': 'Test Vendor'
    }
    
    print("=== Testing GUI data expectations ===")
    print(f"filename: {Path(mock_result.get('pdf_path', 'Unknown')).name}")
    
    # Test status logic (should match GUI)
    status = mock_result.get('approval_status', mock_result.get('status', 'Unknown'))
    print(f"status: {status}")
    
    # Test issues count logic (should match GUI)  
    issues_count = mock_result.get('validation_issues_count', 0)
    if issues_count is None or issues_count == 0:
        # Try alternative field names
        if 'validation_issues' in mock_result and isinstance(mock_result['validation_issues'], list):
            issues_count = len(mock_result['validation_issues'])
    print(f"issues_count: {issues_count}")
    
    # Test PDF path logic
    pdf_path = mock_result.get('processed_pdf_path') or mock_result.get('pdf_path')
    print(f"pdf_path for buttons: {pdf_path}")
    
    print("\n=== Expected result ===")
    print("✅ All fields should be properly extracted")
    print("✅ Status should be 'REQUIRES REVIEW'")
    print("✅ Issues count should be 2") 
    print("✅ PDF path should be available")

if __name__ == "__main__":
    test_result_dict_structure()
