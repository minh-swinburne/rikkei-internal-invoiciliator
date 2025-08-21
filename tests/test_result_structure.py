#!/usr/bin/env python3
"""Test script to examine ProcessingResult.model_dump() structure"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.workflow import ProcessingResult, ProcessingStatus
from src.core.models import Invoice, PurchaseOrder, ValidationResult, Item

def create_sample_result():
    """Create a sample ProcessingResult to test model_dump() structure."""
    
    # Create sample items
    invoice_item = Item(
        sku="TEST123",
        vpn="VPN456",
        description="Test Product",
        unit_price=100.0,
        quantity_ordered=2,
        quantity_shipped=2,
        total=200.0
    )
    
    po_item = Item(
        sku="TEST123",
        vpn="VPN456", 
        description="Test Product",
        unit_price=100.0,
        quantity_ordered=2,
        total=200.0
    )
    
    # Create sample invoice
    invoice = Invoice(
        invoice_number="INV-123",
        po_number="PO-456",
        vendor="Test Vendor",
        items=[invoice_item]
    )
    
    # Create sample PO
    po = PurchaseOrder(
        po_number="PO-456",
        items=[po_item]
    )
    
    # Create validation result
    validation = ValidationResult(
        is_approved=False,
        vendor="Test Vendor",
        issues=["Test issue"],
        total_invoice_amount=200.0,
        total_po_amount=200.0
    )
    
    # Create ProcessingResult
    result = ProcessingResult(
        pdf_path=Path("test.pdf"),
        status=ProcessingStatus.COMPLETED,
        started_at=datetime.now(),
        invoice=invoice,
        purchase_order=po,
        validation_result=validation,
        approval_status="REQUIRES REVIEW"
    )
    result.mark_completed(success=True)
    
    return result

def main():
    print("=== Testing ProcessingResult.model_dump() structure ===")
    
    # Create sample result
    result = create_sample_result()
    
    # Get dict representation
    result_dict = result.model_dump()
    
    # Print structure
    print("\nFull model_dump() structure:")
    print(json.dumps(result_dict, indent=2, default=str))
    
    # Print key fields that GUI expects
    print("\n=== Key fields for GUI ===")
    print(f"pdf_path: {result_dict.get('pdf_path')}")
    print(f"status: {result_dict.get('status')}")
    print(f"approval_status: {result_dict.get('approval_status')}")
    print(f"validation_issues_count: {result_dict.get('validation_issues_count')}")
    print(f"processed_pdf_path: {result_dict.get('processed_pdf_path')}")
    print(f"is_approved: {result_dict.get('is_approved')}")
    
    print("\n=== Alternative field names ===")
    print(f"validation_issues (if exists): {result_dict.get('validation_issues', 'NOT FOUND')}")
    print(f"issues_count (if exists): {result_dict.get('issues_count', 'NOT FOUND')}")

if __name__ == "__main__":
    main()
