from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    """Item model for both invoice and purchase order items"""
    sku: Optional[str] = None
    vpn: Optional[str] = None
    description: str
    unit_price: float = Field(ge=0.0, description="Unit price must be non-negative")
    quantity_ordered: int = Field(ge=0, description="Ordered quantity must be non-negative")
    quantity_shipped: Optional[int] = Field(None, ge=0, description="Shipped quantity (optional for POs)")
    total: float = Field(ge=0.0, description="Total price must be non-negative")
    
    def get_identifier(self) -> str:
        """Get a unique identifier for item matching"""
        if self.sku:
            return f"sku:{self.sku}"
        elif self.vpn:
            return f"vpn:{self.vpn}"
        else:
            return f"desc:{self.description.lower().strip()}"

class PurchaseOrder(BaseModel):
    """Purchase Order model"""
    po_number: str
    items: list[Item]
    extra_fees: dict[str, float] = Field(default_factory=dict)
    
    def get_item_by_identifier(self, identifier: str) -> Optional[Item]:
        """Find item by SKU, VPN, or description"""
        for item in self.items:
            if item.get_identifier() == identifier:
                return item
        return None

class Invoice(BaseModel):
    """Invoice model"""
    invoice_number: str
    po_number: str
    items: list[Item]
    extra_fees: dict[str, float] = Field(default_factory=dict)
    is_credit_memo: bool = False
    
    def get_item_by_identifier(self, identifier: str) -> Optional[Item]:
        """Find item by SKU, VPN, or description"""
        for item in self.items:
            if item.get_identifier() == identifier:
                return item
        return None

class ValidationResult(BaseModel):
    """Result of invoice validation"""
    approved: bool
    reason: Optional[str] = None
    manual_review: bool = False
    details: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
