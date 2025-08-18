"""
Business rule validation for invoice and purchase order reconciliation.
"""

from typing import List

from .models import Invoice, PurchaseOrder, ValidationResult
from .logging_config import get_module_logger


class InvoiceValidator:
    """Validates invoice and purchase order data according to business rules."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = get_module_logger('validator')
    
    def validate(self, invoice: Invoice, purchase_order: PurchaseOrder) -> ValidationResult:
        """
        Validate invoice against purchase order according to business rules.
        
        Args:
            invoice: Invoice data
            purchase_order: Purchase order data
            
        Returns:
            ValidationResult with approval status and any issues found
        """
        self.logger.info(f"Validating invoice {invoice.invoice_number} against PO {purchase_order.po_number}")
        
        issues: List[str] = []
        
        # Rule 1: PO numbers must match
        if invoice.po_number != purchase_order.po_number:
            issues.append(f"PO number mismatch: Invoice {invoice.po_number} vs PO {purchase_order.po_number}")
            self.logger.warning(f"PO number mismatch: {invoice.po_number} vs {purchase_order.po_number}")
        
        # Rule 2: Validate items
        invoice_items = {item.sku: item for item in invoice.items if item.sku}
        po_items = {item.sku: item for item in purchase_order.items if item.sku}
        
        for sku, invoice_item in invoice_items.items():
            if sku not in po_items:
                issues.append(f"Item {sku} in invoice but not in PO")
                self.logger.warning(f"Item {sku} in invoice but not in PO")
                continue
            
            po_item = po_items[sku]
            
            # Rule 3: Unit prices must match
            if invoice_item.unit_price != po_item.unit_price:
                issues.append(f"Unit price mismatch for {sku}: Invoice ${invoice_item.unit_price} vs PO ${po_item.unit_price}")
                self.logger.warning(f"Unit price mismatch for {sku}: ${invoice_item.unit_price} vs ${po_item.unit_price}")
            
            # Rule 4: Partial deliveries are acceptable (shipped <= ordered)
            if invoice_item.quantity_shipped and invoice_item.quantity_shipped > po_item.quantity_ordered:
                issues.append(f"Over-shipment for {sku}: Shipped {invoice_item.quantity_shipped} vs Ordered {po_item.quantity_ordered}")
                self.logger.warning(f"Over-shipment for {sku}: {invoice_item.quantity_shipped} vs {po_item.quantity_ordered}")
        
        # Rule 5: Check for items in PO but not in invoice (informational)
        for sku in po_items:
            if sku not in invoice_items:
                issues.append(f"Item {sku} in PO but not delivered in invoice (partial delivery)")
                self.logger.info(f"Partial delivery: Item {sku} in PO but not in invoice")
        
        # Rule 6: Check for missing critical identifiers
        if not invoice.invoice_number:
            issues.append("Missing invoice number")
            self.logger.error("Missing invoice number")
        
        if not purchase_order.po_number:
            issues.append("Missing PO number")
            self.logger.error("Missing PO number")
        
        # Rule 7: Detect credit memos (require manual review)
        if any("credit" in str(item.description).lower() for item in invoice.items if item.description):
            issues.append("Credit memo detected - requires manual review")
            self.logger.warning("Credit memo detected")
        
        result = ValidationResult(
            is_approved=len(issues) == 0,
            issues=issues,
            total_invoice_amount=sum(
                (item.quantity_shipped or 0) * item.unit_price 
                for item in invoice.items 
                if item.unit_price
            ),
            total_po_amount=sum(
                item.quantity_ordered * item.unit_price 
                for item in purchase_order.items 
                if item.unit_price
            )
        )

        status = "APPROVED" if result.is_approved else "REQUIRES REVIEW"
        self.logger.info(f"Validation complete: {status} - {len(issues)} issues found")
        
        return result


# Backward compatibility - keep the original function
def validate_invoice_po(invoice: Invoice, po: PurchaseOrder) -> ValidationResult:
    """Legacy function for backward compatibility"""
    validator = InvoiceValidator()
    return validator.validate(invoice, po)
