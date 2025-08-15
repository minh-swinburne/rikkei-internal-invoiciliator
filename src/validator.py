import logging
from .models import Invoice, PurchaseOrder, ValidationResult

logger = logging.getLogger(__name__)

def validate_invoice_po(invoice: Invoice, po: PurchaseOrder) -> ValidationResult:
    """Validate invoice against purchase order according to business rules"""
    warnings = []
    errors = []
    
    # Rule 1: PO number must match
    if invoice.po_number != po.po_number:
        errors.append(f"PO number mismatch: Invoice {invoice.po_number} vs PO {po.po_number}")
        return ValidationResult(
            approved=False, 
            reason="PO number mismatch", 
            manual_review=True,
            errors=errors
        )

    # Rule 2: Item matching by SKU or VPN
    unmatched_items = []
    for inv_item in invoice.items:
        match = po.get_item_by_identifier(inv_item.get_identifier())
        
        if not match:
            unmatched_items.append(inv_item)
            continue
            
        # Rule 3: Unit price must match (with small tolerance for rounding)
        price_tolerance = 0.01
        if abs(inv_item.unit_price - match.unit_price) > price_tolerance:
            errors.append(f"Unit price mismatch for {inv_item.get_identifier()}: "
                         f"Invoice ${inv_item.unit_price} vs PO ${match.unit_price}")
        
        # Rule 4: Quantity validation
        if inv_item.quantity_shipped is not None:
            # Check if shipped quantity exceeds ordered quantity
            if inv_item.quantity_shipped > match.quantity_ordered:
                errors.append(f"Shipped quantity ({inv_item.quantity_shipped}) exceeds "
                             f"ordered quantity ({match.quantity_ordered}) for {inv_item.description}")
            
            # Warn about partial shipments
            elif inv_item.quantity_shipped < match.quantity_ordered:
                warnings.append(f"Partial shipment: {inv_item.quantity_shipped} of "
                               f"{match.quantity_ordered} for {inv_item.description}")

    # Rule 5: Credit memo handling
    if invoice.is_credit_memo:
        warnings.append("Invoice is a credit memo - manual review recommended")
        return ValidationResult(
            approved=False, 
            reason="Credit memo detected", 
            manual_review=True,
            warnings=warnings
        )
    
    # Rule 6: Check for unmatched items
    if unmatched_items:
        unmatched_descriptions = [item.description for item in unmatched_items]
        errors.append("Unmatched items found in invoice")
        return ValidationResult(
            approved=False, 
            reason="Unmatched items present", 
            manual_review=True,
            details=f"Unmatched items: {', '.join(unmatched_descriptions)}",
            errors=errors,
            warnings=warnings
        )
    
    # Rule 7: If there are any errors, require manual review
    if errors:
        return ValidationResult(
            approved=False, 
            reason="Validation errors found", 
            manual_review=True,
            errors=errors,
            warnings=warnings
        )
    
    # All validations passed
    return ValidationResult(
        approved=True, 
        reason="Invoice matches PO", 
        manual_review=False,
        warnings=warnings
    )
